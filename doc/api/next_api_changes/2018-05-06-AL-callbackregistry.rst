`CallbackRegistry` now stores callbacks using stdlib's `WeakMethods`
````````````````````````````````````````````````````````````````````

In particular, this implies that ``CallbackRegistry.callbacks[signal]`` is now
a mapping of callback ids to `WeakMethods` (i.e., they need to be first called
with no arguments to retrieve the method itself).
