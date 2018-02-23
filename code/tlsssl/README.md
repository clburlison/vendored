# NO LONGER USEFUL FOR 10.13
This is based on the proof of concept work done by [@pudquick](https://github.com/pudquick) here https://github.com/pudquick/tlsssl

This hack only useful for machines <10.13. With 10.13 Apple has linked python against LibreSSL so we gain TLS 1.2 support out of the box (see below).


# Sample TLS outputs

## Stock 10.13

```bash
$ /usr/bin/python tests/version_tester.py
Our python is located: /usr/bin/python
Our python version: 2.7.10
Our openssl is: LibreSSL 2.2.7
------------------------------------------------------------------
SUCCESS: Connection was made using TLS 1.2
```

## Using a vendored Python version

```bash
Our python is located: /Library/vendored/Python/2.7/bin/python
Our python version: 2.7.14
Our openssl is: OpenSSL 1.0.2n  7 Dec 2017
------------------------------------------------------------------
SUCCESS: Connection was made using TLS 1.2
```

## Using this tlsssl patch on 10.12.6

```bash
Our python is located: /usr/bin/python
Our python version: 2.7.10
Our openssl is: OpenSSL 1.0.2k  26 Jan 2017
------------------------------------------------------------------
SUCCESS: Connection was made using TLS 1.2
```
