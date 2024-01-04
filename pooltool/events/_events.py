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
        description="Null event",
    )


def ball_ball_collision(
    ball1: Ball, ball2: Ball, time: float, set_initial: bool = False
) -> Event:

    position = (ball1.xyz + ball2.xyz) / 2
    position = f"({position[0]:.2f},{position[1]:.2f})"

    return Event(
        event_type=EventType.BALL_BALL,
        agents=(
            Agent.from_object(ball1, set_initial=set_initial),
            Agent.from_object(ball2, set_initial=set_initial),
        ),
        time=time,
        description = f"Ball {ball1.id} collided with ball {ball2.id} at {position}.",
    )


def ball_linear_cushion_collision(
    ball: Ball, cushion: LinearCushionSegment, time: float, set_initial: bool = False
) -> Event:
    return Event(
        event_type=EventType.BALL_LINEAR_CUSHION,
        agents=(
            Agent.from_object(ball, set_initial=set_initial),
            Agent.from_object(cushion, set_initial=set_initial),
        ),
        time=time,
        description=f"Ball {ball.id} collided with cushion {cushion.id}.",
    )


def ball_circular_cushion_collision(
    ball: Ball, cushion: CircularCushionSegment, time: float, set_initial: bool = False
) -> Event:
    return Event(
        event_type=EventType.BALL_CIRCULAR_CUSHION,
        agents=(
            Agent.from_object(ball, set_initial=set_initial),
            Agent.from_object(cushion, set_initial=set_initial),
        ),
        time=time,
        description=f"Ball {ball.id} collided with cushion {cushion.id}.",
    )


def ball_pocket_collision(
    ball: Ball, pocket: Pocket, time: float, set_initial: bool = False
) -> Event:
    return Event(
        event_type=EventType.BALL_POCKET,
        agents=(
            Agent.from_object(ball, set_initial=set_initial),
            Agent.from_object(pocket, set_initial=set_initial),
        ),
        time=time,
        description=f"Ball {ball.id} fell into pocket {pocket.id}.",
    )


def stick_ball_collision(
    stick: Cue, ball: Ball, time: float, set_initial: bool = False
) -> Event:
    
    pos = f"({ball.xyz[0]:.2f},{ball.xyz[1]:.2f})"

    return Event(
        event_type=EventType.STICK_BALL,
        agents=(
            Agent.from_object(stick, set_initial=set_initial),
            Agent.from_object(ball, set_initial=set_initial),
        ),
        time=time,
        description=f"Stick {stick.id} collided with ball {ball.id} at position {pos}.",
    )


def spinning_stationary_transition(
    ball: Ball, time: float, set_initial: bool = False
) -> Event:
    return Event(
        event_type=EventType.SPINNING_STATIONARY,
        agents=(Agent.from_object(ball, set_initial=set_initial),),
        time=time,
        description=f"Ball {ball.id} transitioned from spinning to stationary.",
    )


def rolling_stationary_transition(
    ball: Ball, time: float, set_initial: bool = False
) -> Event:
    return Event(
        event_type=EventType.ROLLING_STATIONARY,
        agents=(Agent.from_object(ball, set_initial=set_initial),),
        time=time,
        description=f"Ball {ball.id} transitioned from rolling to stationary.",
    )


def rolling_spinning_transition(
    ball: Ball, time: float, set_initial: bool = False
) -> Event:
    return Event(
        event_type=EventType.ROLLING_SPINNING,
        agents=(Agent.from_object(ball, set_initial=set_initial),),
        time=time,
        description=f"Ball {ball.id} transitioned from rolling to spinning.",
    )


def sliding_rolling_transition(
    ball: Ball, time: float, set_initial: bool = False
) -> Event:
    return Event(
        event_type=EventType.SLIDING_ROLLING,
        agents=(Agent.from_object(ball, set_initial=set_initial),),
        time=time,
        description=f"Ball {ball.id} transitioned from sliding to rolling.",
    )
