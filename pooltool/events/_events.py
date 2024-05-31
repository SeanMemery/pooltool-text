from __future__ import annotations

from pooltool.events.datatypes import Agent, Event, EventType
from pooltool.objects.ball.datatypes import Ball
from pooltool.objects.cue.datatypes import Cue
from pooltool.objects.datatypes import NullObject
from pooltool.objects.table.components import (
    CircularCushionSegment,
    LinearCushionSegment,
    Pocket,
)


def null_event(time: float, set_initial: bool = False) -> Event:
    return Event(
        event_type=EventType.NONE,
        agents=(Agent.from_object(NullObject(), set_initial=set_initial),),
        time=time,
        typ_obj=("", "", ""),
        description="Null event",
    )


def ball_ball_collision(
    ball1: Ball, ball2: Ball, time: float, set_initial: bool = False
) -> Event:

    position = (ball1.xyz + ball2.xyz) / 2
    position = f"({abs(position[0]):.2f},{abs(position[1]):.2f})"

    return Event(
        event_type=EventType.BALL_BALL,
        agents=(
            Agent.from_object(ball1, set_initial=set_initial),
            Agent.from_object(ball2, set_initial=set_initial),
        ),
        time=time,
        typ_obj=("ball-ball", f"{ball1.id}-{ball2.id}", position),
        description = f"Ball {ball1.id} collided with ball {ball2.id}.",
    )


def ball_linear_cushion_collision(
    ball: Ball, cushion: LinearCushionSegment, time: float, set_initial: bool = False
) -> Event:
    
    position = ball.xyz
    position = f"({abs(position[0]):.2f},{abs(position[1]):.2f})"

    return Event(
        event_type=EventType.BALL_LINEAR_CUSHION,
        agents=(
            Agent.from_object(ball, set_initial=set_initial),
            Agent.from_object(cushion, set_initial=set_initial),
        ),
        time=time,
        typ_obj=("ball-cushion", f"{ball.id}-{cushion.id}", position),
        description=f"Ball {ball.id} collided with cushion.",
    )


def ball_circular_cushion_collision(
    ball: Ball, cushion: CircularCushionSegment, time: float, set_initial: bool = False
) -> Event:
    
    position = ball.xyz
    position = f"({abs(position[0]):.2f},{abs(position[1]):.2f})"

    return Event(
        event_type=EventType.BALL_CIRCULAR_CUSHION,
        agents=(
            Agent.from_object(ball, set_initial=set_initial),
            Agent.from_object(cushion, set_initial=set_initial),
        ),
        time=time,
        typ_obj=("ball-cushion", f"{ball.id}-{cushion.id}", position),
        description=f"Ball {ball.id} collided with cushion.",
    )


def ball_pocket_collision(
    ball: Ball, pocket: Pocket, time: float, set_initial: bool = False
) -> Event:
    
    # Dict of positions of pockets (so that theyre rounded for simplicity)
    position = {
        "dummy": (-1.00, -1.00),
        "lb": (0.00, 0.00),
        "lc": (0.00, 1.00),
        "lt": (0.00, 2.00),
        "rb": (1.00, 0.00),
        "rc": (1.00, 1.00),
        "rt": (1.00, 2.00)
    }[pocket.id]
    position = f"({abs(position[0]):.2f},{abs(position[1]):.2f})"

    return Event(
        event_type=EventType.BALL_POCKET,
        agents=(
            Agent.from_object(ball, set_initial=set_initial),
            Agent.from_object(pocket, set_initial=set_initial),
        ),
        time=time,
        typ_obj=("ball-pocket", f"{ball.id}-{pocket.id}", position),
        description=f"Ball {ball.id} fell into pocket {pocket.id}.",
    )


def stick_ball_collision(
    stick: Cue, ball: Ball, time: float, set_initial: bool = False
) -> Event:
    
    position = f"({abs(ball.xyz[0]):.2f},{abs(ball.xyz[1]):.2f})"

    return Event(
        event_type=EventType.STICK_BALL,
        agents=(
            Agent.from_object(stick, set_initial=set_initial),
            Agent.from_object(ball, set_initial=set_initial),
        ),
        time=time,
        typ_obj=("stick-ball", f"stick-{ball.id}", position),
        description=f"Stick {stick.id} collided with ball {ball.id}.",
    )


def spinning_stationary_transition(
    ball: Ball, time: float, set_initial: bool = False
) -> Event:
    
    position = ball.xyz
    position = f"({abs(position[0]):.2f},{abs(position[1]):.2f})"

    return Event(
        event_type=EventType.SPINNING_STATIONARY,
        agents=(Agent.from_object(ball, set_initial=set_initial),),
        time=time,
        typ_obj=("ball-stop",f"{ball.id}-{ball.id}",position),
        description=f"Ball {ball.id} transitioned from spinning to stationary.",
    )


def rolling_stationary_transition(
    ball: Ball, time: float, set_initial: bool = False
) -> Event:
    
    position = ball.xyz
    position = f"({abs(position[0]):.2f},{abs(position[1]):.2f})"

    return Event(
        event_type=EventType.ROLLING_STATIONARY,
        agents=(Agent.from_object(ball, set_initial=set_initial),),
        time=time,
        typ_obj=("ball-stop",f"{ball.id}-{ball.id}",position),
        description=f"Ball {ball.id} transitioned from rolling to stationary.",
    )


def rolling_spinning_transition(
    ball: Ball, time: float, set_initial: bool = False
) -> Event:
    
    position = ball.xyz
    position = f"({abs(position[0]):.2f},{abs(position[1]):.2f})"

    return Event(
        event_type=EventType.ROLLING_SPINNING,
        agents=(Agent.from_object(ball, set_initial=set_initial),),
        time=time,
        typ_obj=("","",""),
        description=f"Ball {ball.id} transitioned from rolling to spinning.",
    )


def sliding_rolling_transition(
    ball: Ball, time: float, set_initial: bool = False
) -> Event:
    
    position = ball.xyz
    position = f"({abs(position[0]):.2f},{abs(position[1]):.2f})"

    return Event(
        event_type=EventType.SLIDING_ROLLING,
        agents=(Agent.from_object(ball, set_initial=set_initial),),
        time=time,
        typ_obj=("","",""),
        description=f"Ball {ball.id} transitioned from sliding to rolling.",
    )
