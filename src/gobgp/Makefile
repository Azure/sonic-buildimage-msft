export GOPATH=/tmp/go

INSTALL := /usr/bin/install

all: gobgp gobgpd

gobgp_prepare:
	git clone https://github.com/osrg/gobgp.git
	cd gobgp && /usr/local/go/bin/go mod download

gobgpd: gobgp_prepare
	cd gobgp && /usr/local/go/bin/go install ./cmd/gobgpd

gobgp: gobgp_prepare
	cd gobgp && /usr/local/go/bin/go install ./cmd/gobgp

install:
	$(INSTALL) -D ${GOPATH}/bin/gobgp $(DESTDIR)/usr/bin/gobgp
	$(INSTALL) -D ${GOPATH}/bin/gobgpd $(DESTDIR)/usr/sbin/gobgpd
	$(INSTALL) -D gobgpd.conf.sample $(DESTDIR)/etc/gobgp/gobgpd.conf.sample

deinstall:
	rm $(DESTDIR)/usr/bin/gobgp
	rm $(DESTDIR)/usr/sbin/gobgpd

clean:
	rm -fr ${GOPATH}
	rm -fr gobgp
