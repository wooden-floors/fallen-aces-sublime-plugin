## SetLocalVariable(name, value)
Sets a local variable that can be read from the same script.

**How to use**
```fallen
SetLocalVariable("phone_is_ringing", 1);

If(Equal("phone_is_ringing", 1))
{
    ...
}
```

## SetWorldVariable(name, value)
Sets a world variable that can be read from other scripts.

**How to use**
```fallen
SetWorldVariable("phone_is_ringing", 1);

If(Equal("phone_is_ringing", 1))
{
    ...
}
```

## SetState(entityTag, stateName)
Sets entity state.

**How to use**
```fallen
SetWorldVariable("delia", 40);
SetState("delia", "&Sleeping");

// Delia states:
// - "&Sleeping"

// Goon states:
// - "Shitting"

```


## Equal(name, value)
Compares variable state with given value and returns `true` if equal, `false` otherwise.

**How to use**

```fallen
If(Equal("door_open", 1))
{
    ...
}
```

## PlayAnimation(entityTag, animationName)
Play entity animation.

**How to use**
```fallen
SetWorldVariable("nightwave", 19);
PlayAnimation("nightwave", "Stand - Injured - Idle");

// Nigthwave animations:
// - "Stand - Injured - Idle"
// - "Sit - Injured - Idle"

// Blake animations:
// - "Idle"
```

## CreateDisturbance(disturbanceTypeName, positionEntityTag, entityInteractedWithTag)
Create disturbance that enemies will investigate.

Position of `positionEntityTag` is used as disturbance position.
`entityInteractedWithTag` is an entity that was interacted with to create a disturbance.

**How to use**
```fallen
// 133 - tag of shopbell, 94 - tag of used door
CreateDisturbance("SomethingTurnedOn", 133, 94); 

// Disturbance types:
// - SomethingTurnedOn
// - SomethingTurnedOff
```

## GetHitpointsNormalised(entityTag, outputVariable)
Set a `outputVariable` with the current hitpoints of an enemy normalized between 0-1 (1 being full health).

**How to use**
```fallen
GetHitpointsNormalised("delia", "delia_normalised_hitpoints");

If (LessOrEqual("delia_normalised_hitpoints", 0))
{
    ...
}

If (Greater("delia_normalised_hitpoints", 0.8))
{
    ...
}
```
