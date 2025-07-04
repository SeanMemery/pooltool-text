#! /usr/bin/env python

import gc
import sys
from functools import partial
from typing import Generator, Optional, Tuple, cast

import gltf  # FIXME at first glance this does nothing?
import simplepbr
from attrs import define
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    ClockObject,
    FrameBufferProperties,
    GraphicsWindow,
    TextNode,
    WindowProperties,
)

import pooltool.ani as ani
import pooltool.ani.tasks as tasks
import pooltool.ani.utils as autils
import pooltool.terminal as terminal
from pooltool.ani.camera import cam
from pooltool.ani.collision import cue_avoid
from pooltool.ani.environment import environment
from pooltool.ani.globals import Global, require_showbase
from pooltool.ani.hud import HUDElement, hud
from pooltool.ani.menu import GenericMenu, menus
from pooltool.ani.modes import Mode, ModeManager, all_modes
from pooltool.ani.mouse import mouse
from pooltool.evolution.continuize import continuize
from pooltool.game.datatypes import GameType
from pooltool.game.layouts import get_rack
from pooltool.game.ruleset import get_ruleset
from pooltool.objects.cue.datatypes import Cue
from pooltool.objects.table.datatypes import Table
from pooltool.system.datatypes import System, multisystem
from pooltool.system.render import PlaybackMode, visual
from pooltool.utils import get_total_memory_usage


@define
class ShowBaseConfig:
    window_type: Optional[str] = None
    window_size: Optional[Tuple[int, int]] = None
    fb_prop: Optional[FrameBufferProperties] = None
    monitor: bool = False

    @classmethod
    def default(cls):
        return cls(
            window_type="onscreen",
            window_size=None,
            fb_prop=None,
            monitor=False,
        )


@require_showbase
def boop(frames=1):
    """Advance/render a number of frames"""
    for _ in range(frames):
        Global.base.graphicsEngine.renderFrame()


@require_showbase
def window_task(win=None):
    """Routine for managing window activity/resizing

    Determines whether window is active or not. If not, purgatory mode is entered, a
    reduced FPS state.

    The user can modify the game window to be whatever size they want. Ideally, they
    would be able to pick arbitrary aspect ratios, however this project has been
    hardcoded to run at a specific aspect ratio, otherwise it looks
    stretched/squished.

    With that in mind, this method is called whenever a change to the window occurs,
    and essentially fixes the aspect ratio. For any given window size chosen by the
    user, this will override their resizing, and resize the window to one with an
    area equal to that requested, but at the required aspect ratio.
    """
    is_window_active = Global.base.win.get_properties().foreground
    if not is_window_active and Global.mode_mgr.mode != Mode.purgatory:
        Global.mode_mgr.change_mode(Mode.purgatory)

    requested_width = Global.base.win.getXSize()
    requested_height = Global.base.win.getYSize()

    diff = abs(requested_width / requested_height - ani.aspect_ratio)
    if diff / ani.aspect_ratio < 0.05:
        # If they are within 5% of the intended ratio, just let them be.
        return

    requested_area = requested_width * requested_height

    # A = w*h
    # A = r*h*h
    # h = (A/r)^(1/2)
    height = (requested_area / ani.aspect_ratio) ** (1 / 2)
    width = height * ani.aspect_ratio

    properties = WindowProperties()
    properties.setSize(int(width), int(height))
    Global.base.win.requestProperties(properties)


def _resize_offscreen_window(size: Tuple[int, int]):
    """Changes window size when provided the dimensions (x, y) in pixels"""
    Global.base.win.setSize(*[int(dim) for dim in size])


class Interface(ShowBase):
    def __init__(self, config: ShowBaseConfig):
        super().__init__(self, windowType=config.window_type)

        self.openMainWindow(fbprops=config.fb_prop, size=config.window_size)

        # Background doesn't apply if ran after simplepbr.init(). See
        # https://discourse.panda3d.org/t/cant-change-base-background-after-simplepbr-init/28945
        Global.base.setBackgroundColor(0.04, 0.04, 0.04)

        simplepbr.init(
            enable_shadows=ani.settings["graphics"]["shadows"], max_lights=13
        )

        if isinstance(self.win, GraphicsWindow):
            mouse.init()

        cam.init()

        if not ani.settings["graphics"]["shader"]:
            Global.render.set_shader_off()

        Global.clock.setMode(ClockObject.MLimited)
        Global.clock.setFrameRate(ani.settings["graphics"]["fps"])

        Global.register_mode_mgr(ModeManager(all_modes))
        assert Global.mode_mgr is not None
        Global.mode_mgr.init_modes()

        self.frame = 0
        tasks.add(self.increment_frame, "increment_frame")

        if config.monitor:
            tasks.add(self.monitor, "monitor")

        self.listen_constant_events()
        self.stdout = terminal.Run()

    def listen_constant_events(self):
        """Listen for events that are mode independent"""
        tasks.register_event("window-event", window_task)
        tasks.register_event("close-scene", self.close_scene)
        tasks.register_event("toggle-help", hud.toggle_help)

    def close_scene(self):
        visual.teardown()

        environment.unload_room()
        environment.unload_lights()

        hud.destroy()

        multisystem.reset()

        cam.fixation = None
        cam.fixation_object = None
        cam.fixated = False

        gc.collect()

    def create_scene(self):
        """Create a scene from multisystem"""
        Global.render.attachNewNode("scene")

        visual.attach_system(multisystem.active)
        visual.buildup()

        environment.init(multisystem.active.table)

        R = max([ball.params.R for ball in multisystem.active.balls.values()])
        cam.fixate(
            pos=(multisystem.active.table.w / 2, multisystem.active.table.l / 2, R),
            node=visual.table.get_node("table"),
        )

    def monitor(self, task):
        if Global.mode_mgr.mode == Mode.purgatory or Global.mode_mgr.mode is None:
            return task.cont

        keymap = Global.mode_mgr.get_keymap()

        header = partial(self.stdout.warning, "", lc="green", nl_before=1, nl_after=0)
        header(header=f"Frame {self.frame}")

        self.stdout.info("Mode", Global.mode_mgr.mode)
        self.stdout.info("Last", Global.mode_mgr.last_mode)
        self.stdout.info("Tasks", [task.name for task in Global.task_mgr.getAllTasks()])
        self.stdout.info("Memory", get_total_memory_usage())
        self.stdout.info("Actions", [k for k in keymap if keymap[k]])
        self.stdout.info("Keymap", Global.mode_mgr.get_keymap())
        self.stdout.info("Frame", self.frame)

        return task.cont

    def increment_frame(self, task):
        self.frame += 1
        return task.cont

    def finalizeExit(self):
        """Override ShowBase.finalizeExit to potentially prevent sys.exit call

        See:
        https://docs.panda3d.org/1.10/python/reference/direct.showbase.ShowBase#direct.showbase.ShowBase.ShowBase.finalizeExit
        """
        self.stop()

    def stop(self):
        """Called when window exited. Subclasses can avoid by overwriting this method"""
        sys.exit()


FBF_FBP = FrameBufferProperties()
FBF_FBP.setRgbColor(True)
FBF_FBP.setRgbaBits(8, 8, 8, 0)
FBF_FBP.setDepthBits(24)

DEFAULT_FBF_CONFIG = ShowBaseConfig(
    window_type="offscreen",
    monitor=False,
    fb_prop=FBF_FBP,
)


class FrameStepper(Interface):
    """Step through a shot frame-by-frame"""

    def __init__(self, config: ShowBaseConfig = DEFAULT_FBF_CONFIG):
        Interface.__init__(self, config=config)

        # Aim to render 10000 FPS so the clock doesn't sleep between frames
        Global.clock.setMode(ClockObject.MLimited)
        Global.clock.setFrameRate(10000)

    def _iterator(
        self,
        system: System,
        size: Tuple[int, int] = (int(1.6 * 720), 720),
        fps: float = 30.0,
    ) -> Generator:
        continuize(system, dt=1 / fps, inplace=True)

        multisystem.reset()
        multisystem.append(system)

        #_resize_offscreen_window(size)

        self.create_scene()

        # We don't want the cue in this
        visual.cue.hide_nodes()

        # Or the camera fixation point object
        if cam.fixation_object is not None:
            cam.fixation_object.removeNode()

        # Set quaternions for each ball
        for ball in visual.balls.values():
            ball.set_quats(ball._ball.history_cts)

        frames = int(system.events[-1].time * fps) + 1

        yield frames

        for frame in range(frames):
            for ball in visual.balls.values():
                ball.set_render_state_from_history(ball._ball.history_cts, frame)
                ball._ball.state = ball._ball.history_cts[frame]

            Global.task_mgr.step()

            yield frame

    def iterator(self, *args, **kwargs) -> Tuple[Generator, int]:
        """Iterate through each frame

        Args:
            shot:
                The shot you would like to iterate through. It should already by
                simulated. It is OK if you have continuized the shot (you can check with
                shot.continuized), but the continuization will be overwritten to match
                the `fps` chosen in this method.
            size:
                The number of pixels in x and y. If x:y != 1.6, the aspect ratio will
                look distorted.
            fps:
                This is the rate (in frames per second) that the shot is iterated
                through.

        Returns:
            iterator:
                This is an iterator. `next(iterator)` will advance the rendered objects
                to the next frame.
            frames:
                This is the length of the iterator (by the time you receive it). Useful
                for things like `for frame in frames: next(iterator)`.
        """
        iterator = self._iterator(*args, **kwargs)
        frames = next(iterator)
        return iterator, frames


class ShotViewer(Interface):
    """An interface for viewing shots from within a python script"""

    def __init__(self, config=ShowBaseConfig.default()):
        Interface.__init__(self, config=config)
        self.create_standby_screen()
        self.create_title("")

        # Set ShotMode to view only. This prevents giving cue stick control to the user
        # and dictates that esc key closes scene rather than going to a menu
        Global.mode_mgr.modes[Mode.shot].view_only = True

        self.stop()

    def show(self, shot_or_shots=None, title=""):
        multisystem.reset()
        if isinstance(shot_or_shots, System):
            multisystem.append(shot_or_shots)
        else:
            multisystem.extend(shot_or_shots)

        self.create_scene()

        cam.load_saved_state("last_scene", ok_if_not_exists=True)

        self.standby_screen.hide()
        self.create_title(title)
        self.title_node.show()

        if ani.settings["graphics"]["hud"]:
            hud.init(hide=[HUDElement.help_text])

        params = dict(
            build_animations=True,
            playback_mode=PlaybackMode.LOOP,
        )
        Global.mode_mgr.update_event_baseline()
        Global.mode_mgr.change_mode(Mode.shot, enter_kwargs=params)
        Global.task_mgr.run()

    def listen_constant_events(self):
        """Listen for events that are mode independent"""
        Interface.listen_constant_events(self)
        tasks.register_event("stop", self.stop)

    def create_title(self, title):
        self.title_node = autils.CustomOnscreenText(
            text=title,
            pos=(-1.55, -0.93),
            scale=ani.menu_text_scale * 0.7,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            parent=Global.aspect2d,
        )
        self.title_node.hide()

    def create_standby_screen(self):
        self.standby_screen = GenericMenu(frame_color=(0.3, 0.3, 0.3, 1))
        self.standby_screen.add_image(
            ani.logo_paths["default"], pos=(0, 0, 0), scale=(0.5, 1, 0.44)
        )

        autils.CustomOnscreenText(
            text="GUI standing by...",
            style=1,
            fg=(1, 1, 1, 1),
            parent=self.standby_screen.titleMenu,
            align=TextNode.ALeft,
            pos=(-1.55, 0.93),
            scale=0.8 * ani.menu_text_scale,
        )

    def stop(self):
        """Display the standby screen and halt the main loop"""

        self.standby_screen.show()
        self.title_node.hide()

        # Advance a couple of frames to render changes
        boop(2)

        # Stop the main loop
        Global.task_mgr.stop()


class Game(Interface):
    def __init__(self, config=ShowBaseConfig.default()):
        Interface.__init__(self, config=config)

        # FIXME can this be added to MenuMode.enter? It produces a lot of events that
        # end up being part of the baseline due to the update_event_baseline call below.
        # To see, enter debugger after this command check
        # Global.base.messenger.get_events()
        menus.populate()

        # This task chain allows simulations to be run in parallel to the game processes
        Global.task_mgr.setupTaskChain("simulation", numThreads=1)

        tasks.register_event("enter-game", self.enter_game)

        Global.mode_mgr.update_event_baseline()
        Global.mode_mgr.change_mode(Mode.menu)

    def enter_game(self):
        """Close the menu, setup the visualization, and start the game"""
        menus.hide_all()
        self.create_system()
        self.create_scene()
        cue_avoid.init_collisions()

        if ani.settings["graphics"]["hud"]:
            hud.init()

        Global.mode_mgr.change_mode(Mode.aim)

    def create_system(self):
        """Create the multisystem and game objects

        FIXME This is where menu options for game type and further specifications should
        plug into.
        """
        # Change this line to change the game played.
        # Pick from {NINEBALL, EIGHTBALL, THREECUSHION, SNOOKER, SANDBOX}
        game_type = GameType.NINEBALL

        game = get_ruleset(game_type)

        table = Table.from_game_type(game_type)
        balls = get_rack(
            game_type=game_type,
            table=table,
            params=None,
            ballset=None,
            spacing_factor=1e-3,
        )
        cue = Cue(cue_ball_id=game.shot_constraints.cueball(balls))
        shot = System(table=table, balls=balls, cue=cue)

        multisystem.reset()
        multisystem.append(shot)
        Global.game = game

    def start(self):
        Global.task_mgr.run()
