======
dabble
======

In the Dabble language, I kick around some front-end ideas in a consequence-free and low-friction environment.

This is also a mental-health project, where I do…

* Experiment over design
* No worrying
* Nothing that's not fun

The concrete strategy is to implement an interpreter in Python (fast), get the lang how I like it, then either port it to Tinker or else bootstrap directly, reimplementing as a compiler in Dabble itself.


Design Notes
============

Function Scoping
----------------

I prefer function scoping because it lets the programmer work faster and minimizes var declarations, which don't carry much information for humans. Cases where nonlocal writes are desired are exceedingly rare; Python didn't even that option until late in its life. (Though keep an eye on how this works out if we employ mainly closures for encapsulation.) A few instances of ``nonlocal`` are better than the continually noisy pitter-patter of ``var var var``, ``let let let``. I do appreciate being able to lay large amounts of code into a branch of a ``match`` block in OCaml without worrying about state spilling over, but, in that case, it probably improves readability to break that block off as a separate named function anyway. Reporting possible read-before-write vars as errors (to come) stamps out the only intrinsic hazard of function scoping.


Line Comments
-------------

Pro: shebang lines can be automatically considered comments. Con: can't interject a comment in the middle of a line.
