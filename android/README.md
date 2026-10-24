# Olam for Android

A small app that shows an Olam server full screen: the public demo, or your own. The web app is
the whole interface and already fits a phone, so the app only adds what a browser tab can't.

- **First launch** asks for the server. **Public demo** opens https://stuffs.tiresia.xyz/olam/,
  and **Your server** takes your own address. Without `http://` or `https://` it uses https,
  except for an address at home, which rarely has a certificate: an IP address, a port, a name with
  no dot, or one ending in `.local`, `.lan`, `.home` or `.internal` gets http. So
  `olam.example.com` opens https://olam.example.com/, and `192.168.1.20:8462` opens
  http://192.168.1.20:8462/. A path works too, like `example.com/olam/`.
- **Changing it later**: long-press the icon and choose **Server**.
- **The window** is Olam between the status bar and the navigation bar (or the keyboard), on
  Olam's dark ground. **Back** goes back in the page first, and leaves only when there's nowhere
  to go. Links to other sites open in your browser, and **Open in Obsidian** opens Obsidian. Your
  sign-in is kept, for the year Olam's cookie lasts.
- **If the server doesn't answer**, you get its address, **Try again** and **Server**.

The user agent ends in `Olam/<version> (Android shell)`, in case your server wants to know.

## Install it

Each [release](https://github.com/franz-rosenzweig/olam/releases) has `Olam-<version>.apk`. To
have it update itself, add `https://github.com/franz-rosenzweig/olam` to
[Obtainium](https://github.com/ImranR98/Obtainium). It needs Android 11 or newer.

## Build it

You need JDK 17 and the Android SDK with platform 36.

```sh
cd android
./gradlew assembleDebug                   # "Olam dev" (xyz.tiresia.olam.debug), beside the real app, with DevTools
./release.sh path/to/keystore.properties  # Olam-<version>.apk, signed, and its certificate
```

`keystore.properties` has `storeFile` (found beside the properties file), `storePassword`,
`keyAlias` and `keyPassword`. Git ignores it, and any `*.keystore`, `*.jks` and `*.apk` here.

An APK only installs over one signed with the same key, so a build of your own sits beside the
released app only as the debug build. To release one: raise `versionCode` (10000·X + 100·Y + Z)
and `versionName` in `app/build.gradle`, tag the commit `vX.Y.Z` (the same as `versionName`, which
Obtainium compares), build from a fresh clone of the tag, and attach `Olam-X.Y.Z.apk` to the
GitHub release.

## The pieces

| file | |
| --- | --- |
| `MainActivity.java` | the WebView, Back, links that go outside, no answer, the choice of server, and the Server shortcut |
| `Server.java` | the address, what a typed address becomes, and which addresses are the server's |
| `res/layout/main.xml` | the page, the no-answer screen and the chooser |
| `release.sh` | the signed build |

The icon is `web/icon.svg` drawn as vectors, and the fonts are the web app's (IM FELL English and
Alegreya Sans, under the SIL Open Font License in `web/fonts/OFL.txt`).
