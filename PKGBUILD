# Maintainer: icesaviour <https://github.com/icesaviour02-droid>
# Contributor: mohammed160209 <https://github.com/mohammed160209>
pkgname=cra-browser-linux-git
pkgver=1.0.0
pkgrel=1
pkgdesc="Native 1:1 macOS Arc/Cra port for Arch Linux and CachyOS"
arch=('x86_64' 'aarch64')
url="https://github.com/mohammed160209/cra-browser-linux"
license=('MIT')
depends=('electron')
makedepends=('git' 'nodejs' 'npm')
provides=('cra-browser')
conflicts=('cra-browser')
source=("git+https://github.com/mohammed160209/cra-browser-linux.git")
sha256sums=('SKIP')

pkgver() {
    cd "${srcdir}/${pkgname%-git}"
    printf "1.0.0.r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

build() {
    cd "${srcdir}/${pkgname%-git}"
    npm install
    node build.js
}

package() {
    cd "${srcdir}/${pkgname%-git}"

    install -dm755 "${pkgdir}/usr/lib/cra-browser"
    cp -r package.json dist node_modules "${pkgdir}/usr/lib/cra-browser/"

    # Install executable launcher
    install -Dm755 bin/cra-browser "${pkgdir}/usr/bin/cra-browser"

    # Install desktop entry and metainfo
    install -Dm644 data/app.crabrowser.Cra.desktop "${pkgdir}/usr/share/applications/app.crabrowser.Cra.desktop"
    install -Dm644 data/app.crabrowser.Cra.metainfo.xml "${pkgdir}/usr/share/metainfo/app.crabrowser.Cra.metainfo.xml"

    # Install icon
    install -Dm644 data/app.crabrowser.Cra.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/app.crabrowser.Cra.svg"

    # Install blocklist
    install -Dm644 data/blocklist/domains.txt "${pkgdir}/usr/share/cra-browser/blocklist/domains.txt"

    # Install license
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
