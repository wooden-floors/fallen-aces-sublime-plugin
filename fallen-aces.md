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

## Equal(name, value)
Compares variable state with given value and returns `true` if equal, `false` otherwise.

**How to use**

```fallen
If(Equal("door_open", 1))
{
    ...
}
```
