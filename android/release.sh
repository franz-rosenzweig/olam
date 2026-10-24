#!/usr/bin/env bash
# Builds the signed release APK, android/Olam-<version>.apk, and checks its signature.
#
#   ./release.sh                                # signs with android/keystore.properties
#   ./release.sh /path/to/keystore.properties
#
# The properties file (storeFile, storePassword, keyAlias, keyPassword) is read by Gradle alone;
# nothing here prints from it.
set -euo pipefail
cd "$(dirname "$0")"
if [[ -z ${JAVA_HOME:-} && -x /usr/libexec/java_home ]]; then JAVA_HOME=$(/usr/libexec/java_home -v 17); export JAVA_HOME; fi
if [[ -z ${ANDROID_HOME:-} ]]; then
    for d in "${ANDROID_SDK_ROOT:-}" "$HOME/Library/Android/sdk" "$HOME/Android/Sdk" "$HOME/android-sdk"; do
        [[ -n $d && -d $d ]] && { export ANDROID_HOME=$d; break; }
    done
fi
[[ -n ${ANDROID_HOME:-} ]] || { echo "no Android SDK: set ANDROID_HOME" >&2; exit 2; }
SIGNING=${1:-$PWD/keystore.properties}
[[ -f $SIGNING ]] || { echo "no signing properties at $SIGNING" >&2; exit 2; }
SIGNING=$(cd "$(dirname "$SIGNING")" && pwd)/$(basename "$SIGNING")

rm -f app/build/outputs/apk/release/app-release.apk
./gradlew --quiet assembleRelease -PsigningProperties="$SIGNING"
APK=app/build/outputs/apk/release/app-release.apk
[[ -f $APK ]] || { echo "the release build is not signed: check $SIGNING" >&2; exit 1; }
VERSION=$(sed -n "s/.*versionName '\(.*\)'.*/\1/p" app/build.gradle | head -1)
OUT=Olam-$VERSION.apk
cp "$APK" "$OUT"
SIGNER=$(ls -d "$ANDROID_HOME"/build-tools/*/apksigner | sort -V | tail -1)
"$SIGNER" verify --print-certs "$OUT" | grep -E "Signer #1 certificate (DN|SHA-256)"
echo "signed: android/$OUT"
