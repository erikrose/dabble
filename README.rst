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

Indentation-Based Syntax
------------------------

The block-delimiting syntax is whitespace-based for aesthetics and compactness. It is isomorphic to s-expressions and akin to though not inspired by SRFI 49 (which doesn't support partial indents, doesn't enforce returning to the indent level of the parent, and has other differences). The ideal is to slip under the radar of most ALGOL-centric readers but shine when it comes time to metaprogram, store data, or host DSLs. Time will tell whether those use cases pay for the additional cost in ``begin``s (necessary unless the parser is informed ahead of time which params take blocks, e.g. the ``then`` or ``else`` of ``if``).


Line Comments
-------------

Pro: shebang lines can be automatically considered comments. Con: can't interject a comment in the middle of a line.


Modules
-------

One important property of modules in wasm (and JS) is that they don't go grab something from the global namespace; the embedder decides how to resolve the import. Thus, modules take inputs and give outputs (the exported symbols) like a function.

Can we replace modules with functions?

What if a module was just a function that took a list or map of imports and returned a list or map of exports? Module scope becomes the scope of the factory function that returns the exports.

Difficulty: how would a rand module share PRNG state across multiple importers? A ``static`` (or ``one`` or ``singleton``) var declaration?
