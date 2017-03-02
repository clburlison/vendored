Vendored
===

**THIS IS A WORK IN PROGRESS**

Concepts from this repo stem largely from https://github.com/google/macops/tree/master/packages. The goal of this repo make it easy to "vendor" your own frameworks in an easy and automated fashion. This will allow you to have your own version of python, ruby, pyojbc bridge, etc. all in one nice big package or multiple smaller packages.

At least that's the goal when this project is complete.


## Creating a patch
Most of these tools require patch files for compiling. If you're unfamiliar with creating a patch file the basics look a little something like:

```bash
diff -u hello.c hello_new.c > hello.c.patch
```

## Credits
Much thanks to the [Google MacOps](https://github.com/google/macops/) team and [@pudquick](https://github.com/pudquick).
