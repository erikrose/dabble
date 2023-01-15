Function Scoping
----------------

I prefer function scoping because it lets the programmer work faster and because it minimizes var declarations, which are noise. (Cases where nonlocal writes are desired are exceedingly rare; Python didn't even that option until late in its life. A few instances of `nonlocal` are better than the continually noisy pitter-patter of `var var var, let let let`. I do appreciate being able to lay large amounts of code into a branch of a `match` block in OCaml without worrying about state spilling over, but, in that case, it probably improves readability to break that code off as a separate named function. Reporting possible read-before-write vars as errors (to come) stamps out the only intrinsic hazard of function scoping.
