Vendored
===

**THIS IS A WORK IN PROGRESS**

The goal of this repo make it easy to "vendor" your own frameworks and programming languages in an easy and automated fashion.

Once this project is complete you will be able to have own version of python, ruby, pyojbc bridge, openssl, and more all in one nice big package or multiple smaller packages for easy deployment.


## Usage

Currently parts of this project are working. You can run `./build.py` to build and optionally package some of these pieces.

## Creating a patch
Most of these tools require patch files for compiling. If you're unfamiliar with creating a patch file the basics look a little something like:

```bash
diff -u hello.c hello_new.c > hello.c.patch
```

## Credits
Much thanks to the [Google MacOps](https://github.com/google/macops/) team for open sourcing their solution and to [@pudquick](https://github.com/pudquick) for his work on tlsssl so we can patch the native Python 2.7 that comes on macOS.

Based off of works by:

| Author/Organization  |  Project Link |
|----------------------|---------------|
[@pudquick](https://github.com/pudquick) | [pudquick/tlsssl](https://github.com/pudquick/tlsssl)
[Munki](https://github.com/munki) | [munkilib](https://github.com/munki/munki/blob/master/code/client/munkilib/)
[Google Inc.](https://github.com/google/macops) | [google/macops packages](https://github.com/google/macops/tree/master/packages)

## License

This project uses the MIT License.
