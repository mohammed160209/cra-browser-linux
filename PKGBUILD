# Maintainer: icesaviour <https://github.com/icesaviour02-droid>
# Contributor: mohammed160209 <https://github.com/mohammed160209>
pkgname=cra-browser-linux-git
pkgver=0.1.0
pkgrel=1
pkgdesc="Native GTK4 and Libadwaita port of the open-source Cra/Arc browser for Arch Linux and CachyOS"
arch=('x86_64' 'aarch64')
url="https://github.com/mohammed160209/cra-browser-linux"
license=('MIT')
depends=(
    'gtk4'
    'libadwaita'
    'webkitgtk-6.0'
    'python'
    'python-gobject'
)
makedepends=('git' 'python-setuptools' 'python-build' 'python-installer')
provides=('cra-browser')
conflicts=('cra-browser')
source=("git+https://github.com/mohammed160209/cra-browser-linux.git")
sha256sums=('SKIP')

build() {
    cd "${srcdir}/${pkgname%-git}"
    python setup.py build
}

package() {
    cd "${srcdir}/${pkgname%-git}"

    # Install using setuptools into package root
    python setup.py install --root="${pkgdir}" --optimize=1 --skip-build

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
