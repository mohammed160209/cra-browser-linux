pkgname=cra-browser-cef
pkgver=0.2.1
pkgrel=1
pkgdesc='Cra Browser Linux Chromium preview'
arch=('x86_64')
url='https://github.com/mohammed160209/cra-browser-linux'
license=('MIT' 'BSD-3-Clause')
depends=('glibc' 'gcc-libs' 'glib2' 'nss' 'nspr' 'at-spi2-core' 'dbus'
         'libcups' 'libx11' 'libxcomposite' 'libxdamage' 'libxext' 'libxfixes'
         'libxrandr' 'libxcb' 'libxkbcommon' 'mesa' 'expat' 'cairo' 'pango'
         'systemd-libs' 'alsa-lib' 'gtk3')
makedepends=('git' 'cmake' 'ninja')
options=('!strip' '!debug')
_cef='cef_binary_156.0.26+g8ea0c73+chromium-156.0.8078.88_linux64_minimal'
source=('cra-browser-linux::git+https://github.com/mohammed160209/cra-browser-linux.git#branch=chromium-cef-linux'
        "https://cef-builds.spotifycdn.com/${_cef}.tar.bz2")
sha256sums=('SKIP' '600ac0b8f37cb953f884e7c89998a6c200d24959aa74820ad431b61d5ebcf360')

build() {
    cmake -S "$srcdir/cra-browser-linux" -B "$srcdir/build" -G Ninja \
        -DCEF_ROOT="$srcdir/$_cef" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
    cmake --build "$srcdir/build"
}

package() {
    DESTDIR="$pkgdir" cmake --install "$srcdir/build"
    strip --strip-debug "$pkgdir/usr/lib/cra-browser-cef/libcef.so"
}
