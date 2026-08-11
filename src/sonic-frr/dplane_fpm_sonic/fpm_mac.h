// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * Decoding of FPM MAC (AF_BRIDGE neighbour) messages.
 *
 * Kept free of zebra state so it can be unit tested on its own, and so the
 * decode runs on the FPM thread while the caller applies the result on
 * zebra's main thread.
 */
#ifndef _FPM_MAC_H
#define _FPM_MAC_H

#include <stdbool.h>
#include <stdint.h>
#include <linux/rtnetlink.h>

#ifndef ETH_ALEN
#define ETH_ALEN 6
#endif

struct fpm_local_mac {
	int ifindex;
	uint8_t mac[ETH_ALEN];
	uint16_t vid;
	uint32_t generation;
	bool del;
	bool sticky;
};

/*
 * Decode an AF_BRIDGE RTM_NEWNEIGH/RTM_DELNEIGH message. Returns false and
 * leaves *out untouched when the message is not a usable local MAC.
 */
extern bool fpm_mac_decode(const struct nlmsghdr *hdr, struct fpm_local_mac *out);

#endif /* _FPM_MAC_H */
