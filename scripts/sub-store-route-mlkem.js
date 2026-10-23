// Sub-Store ROUTE subscription: inline Script Operator, after source parsing.
// Older 3x-ui exports omit ML-KEM; the installed VLESS URI parser also drops it.
// Complete the three managed nodes here, before ClashMeta serializes them.
function operator(proxies, targetPlatform) {
  const platform = String(targetPlatform).toLowerCase();
  if (!["clashmeta", "clash.meta", "meta", "mihomo"].includes(platform)) {
    return proxies;
  }

  const managedNames = new Set([
    "US-RELAY-TUTUGW",
    "US-9929-TUTUGW",
    "HK-TUTUGW",
  ]);
  for (const proxy of proxies) {
    if (managedNames.has(proxy.name) && proxy.type === "vless" && proxy["reality-opts"]) {
      proxy["client-fingerprint"] = "chrome";
      proxy["reality-opts"]["support-x25519mlkem768"] = true;
    }
  }
  return proxies;
}
