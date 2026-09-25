<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `linux-mac-privilege` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: linux-mac-privilege
title: Linux Mandatory Access Control & Privilege — SELinux, AppArmor & Capabilities
description: >
  The Linux access-control layer above discretionary file permissions: the LSM framework that hosts it, the two
  major MAC systems, and the capability model that decomposes root. Covers the Linux Security Module (LSM) framework
  (hooks fired before each kernel access, the exclusive vs stackable distinction, the modules list SELinux/AppArmor/
  Smack/TOMOYO/Yama/Landlock/IPE/LoadPin/SafeSetID/BPF-LSM, why you cannot run two exclusive modules together, the
  ordered "lsm=" boot stacking); SELinux (the label/context user:role:type:level model, Type Enforcement as the core,
  RBAC and MLS/MCS, the targeted vs MLS policy, enforcing/permissive/disabled modes, domain transitions, booleans,
  file-context and port labeling, the AVC, and the full audit2allow/ausearch/sealert/semanage/restorecon
  troubleshooting loop); AppArmor (the path-based profile model, enforce vs complain mode, abstractions/includes,
  aa-genprof/aa-logprof/aa-complain/aa-enforce, profile flags, attachment, why path-based differs from label-based);
  Linux capabilities (the five thread sets permitted/effective/inheritable/bounding/ambient, the execve()
  transformation formula, file capabilities + securebits + no_new_privs, the dangerous caps CAP_SYS_ADMIN/
  CAP_DAC_OVERRIDE/CAP_SETUID/CAP_NET_ADMIN, getcap/setcap/capsh); and how containers and Kubernetes compose all
  three (cap-drop ALL + add, seLinuxOptions/container_t, AppArmor profiles, Pod Security Standards). Use to choose,
  author, debug, or harden a MAC policy or to reason about least-privilege capability sets.
category: developer
tags: [linux, security, mac, selinux, apparmor, capabilities, lsm, mandatory-access-control, privilege, hardening, containers, devops]
version: "1.0.0"
---

# Linux Mandatory Access Control & Privilege — SELinux, AppArmor & Capabilities

## Overview

Standard Unix permissions are **Discretionary Access Control (DAC)**: the *owner* of a resource decides who may
touch it, and a process running as root (UID 0) bypasses the checks entirely. DAC has two structural weaknesses —
the owner can always loosen access, and a single root-equivalent compromise owns the whole machine. The Linux
access-control stack adds two layers on top of DAC to close those gaps:

- **Mandatory Access Control (MAC)** — a **system-wide policy set by the administrator** that the resource owner
  *cannot* override. Even root is constrained by the policy. On Linux this is implemented by **Linux Security
  Modules (LSM)**, with **SELinux** (label-based) and **AppArmor** (path-based) as the two dominant modules.
- **Capabilities** — decompose the monolithic "root can do anything" privilege into ~40 independent units
  (mount, bind low ports, override file permissions, load kernel modules…), so a process can hold *exactly* the
  privileges it needs and nothing more. This is least-privilege for the root power, orthogonal to MAC.

The access decision for any operation is a **logical AND**: DAC must allow it, **then** every active LSM/MAC policy
must allow it, **then** (for privileged operations) the thread must hold the required capability. Denial by any
layer blocks the operation. This is *defense in depth* — each layer is independent.

```
operation → DAC (owner/perms) AND  capability check (if privileged op)  AND  LSM/MAC hook(s)  → allow/deny
```

For the broader confinement picture (seccomp syscall filtering, Landlock self-sandboxing, gVisor, Kata/Firecracker
microVMs), see `references/linux-sandboxing-confinement.md` — this file is the deep dive on the **MAC + capability**
slice that file only sketches.

## Core Concepts

### 1. The LSM framework — how MAC plugs into the kernel

LSM has been a standard part of the kernel since 2.6. It is **not** a security policy itself; it is a set of
**hooks** placed immediately before the kernel acts on an internal object (open a file, create a socket, check a
capability, exec a binary, etc.). At each hook the kernel calls registered module callbacks; **any** module that
returns denial blocks the action. Hooks are *restrictive* — a module can only **deny** an access DAC already
permitted, never grant one DAC refused (capabilities are the exception that can grant).

- **Approved in-tree modules (as of 2025):** SELinux, AppArmor, Smack, TOMOYO (the "major" MAC modules), plus the
  "minor"/scoped ones: Yama (ptrace scope), LoadPin (pin module/firmware loads to one fs), SafeSetID (constrain
  setuid transitions), Landlock (unprivileged self-sandboxing — see sandboxing ref), IPE (Integrity Policy
  Enforcement), and **BPF LSM** (attach eBPF programs to LSM hooks, since 5.7).
- **Exclusive vs stackable.** SELinux, AppArmor, and Smack set `LSM_FLAG_EXCLUSIVE` — **you can run at most one of
  them at a time.** This is why Ubuntu (AppArmor) and RHEL (SELinux) are an either/or choice, not both. The minor
  modules (Yama, LoadPin, SafeSetID, Landlock) and **BPF LSM are stackable** and run alongside whichever exclusive
  module is active.
- **Ordering / enabling.** Modules initialize in a defined order; the active list and order are controlled at boot
  by the `lsm=` kernel command-line parameter (e.g. `lsm=lockdown,capability,yama,apparmor,bpf`), and
  `CONFIG_LSM` sets the compile-time default. `capability` (the capabilities LSM) is always first so privilege
  checks run before MAC.
- **"Full" general stacking** (running SELinux *and* AppArmor simultaneously) has been worked on for years (Casey
  Schaufler's stacking series) but is **not** mainline as a general feature; treat exclusive MAC as one-at-a-time.

### 2. SELinux — label-based Type Enforcement

SELinux (originally NSA, default on **RHEL/CentOS/Fedora/Rocky/Alma** and Android) attaches a **security context**
(a *label*) to every process and object and decides access by comparing labels against a compiled policy. The
context has four fields:

```
user:role:type:level        e.g.  system_u:object_r:httpd_sys_content_t:s0
                                   unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
```

- **SELinux user** (`_u`) — a policy identity (distinct from the Linux UID), authorized for a set of roles.
- **Role** (`_r`) — an RBAC intermediary; authorizes which **types/domains** a user may enter.
- **Type / domain** (`_t`) — **the heart of SELinux. Type Enforcement (TE)** is the primary mechanism: the type on
  a *process* is its **domain**, the type on a *file/port/object* is its **type**, and policy `allow` rules say
  "domain X may do operation Y to type Z" (e.g. `allow httpd_t httpd_sys_content_t:file { read open getattr };`).
  Anything not explicitly allowed is **denied** (default-deny).
- **Level** (`s0:c0.c1023`) — optional **MLS/MCS** field. **MLS** (Multi-Level Security, Bell-LaPadula) uses
  hierarchical *sensitivities* (s0<s1<…) plus non-hierarchical *categories*: a process may read down and write up
  ("no read up, no write down"). **MCS** (Multi-Category Security) uses only categories and is how container
  runtimes isolate peer containers (each gets a unique category pair).

Key operational concepts:

- **Modes:** `Enforcing` (deny + log), `Permissive` (allow but log what *would* be denied — the debugging mode),
  `Disabled`. Check with `getenforce`; switch live with `setenforce 0|1`; persist in `/etc/selinux/config`
  (`SELINUX=enforcing`). View labels with `ls -Z`, `ps -Z`, `id -Z`.
- **Policy types:** `targeted` (the default — only specific high-risk daemons are confined to tight domains;
  everything else runs in the loose `unconfined_t`) vs `mls` (full multi-level, used in high-security/government).
- **Domain transition:** a process changes domain on `execve()` of a file with the right type, e.g. `init_t`
  running `/usr/sbin/httpd` (labeled `httpd_exec_t`) transitions to `httpd_t`. Requires `type_transition` +
  `allow` rules covering entrypoint/execute/transition.
- **Booleans:** named on/off policy switches that toggle whole behaviors without writing policy — e.g.
  `httpd_can_network_connect`, `httpd_use_nfs`. `getsebool -a`, `setsebool -P httpd_can_network_connect on`
  (`-P` = persistent).
- **Labeling state:** files carry labels in the `security.selinux` xattr. `semanage fcontext` defines the
  *expected* label rules; `restorecon -Rv /path` applies them; `chcon` sets a label ad-hoc (lost on relabel).
  Ports are labeled too: `semanage port -a -t http_port_t -p tcp 8080`.

### 3. SELinux troubleshooting loop (the most common real-world task)

Denials are recorded as **AVC (Access Vector Cache)** messages in the audit log. The canonical workflow:

1. **Find denials:** `ausearch -m avc -ts recent` (or `-ts today`). Each AVC shows `scontext` (source domain),
   `tcontext` (target type), the object class and the `denied { … }` permissions.
2. **Get a human explanation + suggested fix:** `sealert -a /var/log/audit/audit.log` (from `setroubleshoot`)
   translates the raw AVC to English and usually suggests the exact `semanage`/`restorecon`/`setsebool` command.
3. **Apply the *least-invasive* fix in priority order:**
   - **Wrong label?** → `restorecon` (or `semanage fcontext -a -t <type> '<regex>'` then `restorecon`). This is
     the most common root cause (e.g. content served from a non-default path).
   - **A boolean covers it?** → `setsebool -P <bool> on`.
   - **A port needs labeling?** → `semanage port`.
   - **Only if none fit:** generate a custom module with **audit2allow**: `ausearch -m avc -ts recent |
     audit2allow -M mymodule` then `semodule -i mymodule.pp`. Treat audit2allow as a last resort — review the
     generated `allow` rules; blindly installing them can grant more than intended.
- Confirm a problem really is SELinux: flip to `setenforce 0`; if the symptom disappears, it was a denial. **Never
  leave production in permissive/disabled as a "fix."**

### 4. AppArmor — path-based profiles

AppArmor (default on **Ubuntu, Debian, SUSE/openSUSE**) is the other major exclusive MAC module. Instead of
labels, it confines programs by a **profile keyed on the executable's filesystem path** and grants access by the
**paths** the program may touch.

- **A profile** lives in `/etc/apparmor.d/<path.with.dots>` (e.g. `/etc/apparmor.d/usr.sbin.nginx`) and lists
  rules like `/etc/myapp/config r,` (read), `/var/log/myapp/** w,` (write), plus capability and network rules
  (`capability net_bind_service,`, `network inet tcp,`).
- **Abstractions / includes:** reusable rule fragments in `/etc/apparmor.d/abstractions` pulled in with
  `#include <abstractions/base>` (the libc/ld.so/devices baseline every profile needs), `<abstractions/nameservice>`,
  etc. — keeps profiles small.
- **Modes:** **enforce** (violations blocked + logged) and **complain/learning** (violations *only logged*, not
  blocked — used while building a profile). `aa-status` lists profiles and their mode; `aa-enforce`/`aa-complain`
  switch a profile; `aa-disable` unloads it.
- **Building a profile:** `aa-genprof <program>` starts a profile and watches the program in complain mode;
  exercise the app, then `aa-logprof` reads the logged accesses and interactively asks you to allow/deny each,
  refining the profile. Iterate, then switch to enforce. `aa-autodep` stubs an initial profile.
- **Why path-based matters:** simpler to read/write than SELinux, but with a structural caveat — if a file is
  reachable by **multiple paths** (hard links, bind mounts, symlinks), a path rule can be bypassed; AppArmor
  mediates on the *name used*, not an inode label. SELinux labels are immune to this (the label rides the inode).

### 5. Linux capabilities — decomposing root

Capabilities split the all-powerful root privilege into ~40 independent bits (`man 7 capabilities`). Each **thread**
carries **five capability sets**:

| Set | Meaning |
|---|---|
| **Permitted (P)** | The superset the thread *may* use; ceiling for Effective; can't be re-added after drop without execve. |
| **Effective (E)** | The caps the kernel actually checks *right now* for permission decisions. |
| **Inheritable (I)** | Caps preserved across `execve()` **only** if the new file has matching inheritable bits. |
| **Bounding (BND)** | Per-thread ceiling that *masks* what an execve can ever grant; dropping a cap here is permanent for the thread + children. |
| **Ambient (AMB)** | (≥4.3) Caps preserved across `execve()` of an **unprivileged** (no-setuid, no-file-cap) program; invariant: a cap can be ambient only if it is both permitted **and** inheritable. |

**The execve() transformation** (the rule that trips everyone up):

```
P'(ambient)     = (file is privileged) ? 0 : P(ambient)
P'(permitted)   = (P(inheritable) & F(inheritable)) | (F(permitted) & P(bounding)) | P'(ambient)
P'(effective)   = F(effective) ? P'(permitted) : P'(ambient)
P'(inheritable) = P(inheritable)          # unchanged
P'(bounding)    = P(bounding)             # unchanged
```

- **File capabilities** live in the `security.capability` xattr (`F(permitted)`, `F(inheritable)`, and a single
  `F(effective)` bit). They are the modern replacement for setuid-root binaries: `setcap cap_net_bind_service+ep
  /usr/bin/myserver` lets a non-root program bind port 80 without being root. Inspect with `getcap`.
- **Securebits** are per-thread flags that disable the legacy magic of UID 0 — `SECBIT_NOROOT` (root no longer
  auto-gets caps from setuid-root binaries), `SECBIT_KEEP_CAPS`, `SECBIT_NO_SETUID_FIXUP`,
  `SECBIT_NO_CAP_AMBIENT_RAISE`, each with a `LOCKED` variant to make it irreversible.
- **`no_new_privs`** (`prctl(PR_SET_NO_NEW_PRIVS, 1)`): once set, **no execve can ever grant more privilege** —
  setuid bits and file capabilities are ignored. It is the safety latch that makes unprivileged seccomp/Landlock
  self-sandboxing sound, and is set by `NoNewPrivileges=yes` in systemd units and by container runtimes.
- **Capabilities you must respect:**
  - `CAP_SYS_ADMIN` — the "new root": mount, namespace creation, many `setns`/quotactl/keyctl operations. So
    overloaded that holding it ≈ holding root. Avoid granting it to containers.
  - `CAP_DAC_OVERRIDE` — bypass all file read/write/execute DAC checks.
  - `CAP_SETUID` / `CAP_SETGID` — arbitrarily change UIDs/GIDs (forge identity).
  - `CAP_NET_ADMIN` — configure interfaces, routing, firewall, set promiscuous mode.
  - `CAP_NET_BIND_SERVICE` — bind ports < 1024 (the classic legitimate single-cap grant).
  - `CAP_SYS_PTRACE`, `CAP_SYS_MODULE` (load kernel modules), `CAP_BPF`, `CAP_SYS_RAWIO`, `CAP_MKNOD` — all
    high-value escalation targets.
- Tooling: `capsh --print` (decode current sets), `getpcaps <pid>`, `setpriv --bounding-set` / `--ambient-caps`,
  `getcap`/`setcap`.

### 6. How containers and Kubernetes compose MAC + capabilities

Container security is precisely a least-privilege composition of these primitives plus namespaces/cgroups/seccomp:

- **Capabilities:** runtimes start with a small **default-allow** set and you harden by **`--cap-drop=ALL` then
  `--cap-add=<only what's needed>`** (Docker), or in Kubernetes `securityContext.capabilities: { drop: [ALL], add:
  [NET_BIND_SERVICE] }`. Never run `--privileged` (grants all caps + disables seccomp/AppArmor + device access).
- **SELinux:** on RHEL/Podman, containers run in the **`container_t`** domain with content typed
  `container_file_t`, and each container gets a unique **MCS** category pair so one container can't read another's
  files even with the same UID. Kubernetes: `securityContext.seLinuxOptions: { type, level, user, role }`.
- **AppArmor:** Docker ships a default `docker-default` profile; Kubernetes sets it via
  `securityContext.appArmorProfile` (the `container.apparmor.security.beta.kubernetes.io/...` annotation is the
  older form).
- **seccomp:** `RuntimeDefault` adopts the runtime's curated syscall allowlist (blocks ~obscure/dangerous calls).
- **Pod Security Standards** bundle these: the **Baseline** profile forbids privileged pods and restricts
  capabilities/seLinuxOptions; **Restricted** additionally requires `runAsNonRoot`, `seccompProfile:
  RuntimeDefault`, and `drop: [ALL]`. See `references/kubernetes-networking.md` and
  `references/docker-containers.md` for the runtime mechanics, and `references/linux-cgroups-namespaces.md` for the
  underlying namespace/cgroup substrate.

## Practical Patterns

- **Harden a systemd service without writing a MAC policy:** in the unit, set `NoNewPrivileges=yes`,
  `CapabilityBoundingSet=CAP_NET_BIND_SERVICE` (drop everything else), `AmbientCapabilities=CAP_NET_BIND_SERVICE`
  if it runs non-root, plus `ProtectSystem=strict`/`PrivateTmp=yes`. Audit with `systemd-analyze security <unit>`.
  See `references/systemd.md`.
- **Let a non-root binary bind a low port:** `setcap cap_net_bind_service=+ep /path/bin` — no setuid root, no
  capability leaks to children (file caps don't propagate without ambient/inheritable).
- **SELinux: serve web content from a non-standard dir:** `semanage fcontext -a -t httpd_sys_content_t
  "/srv/www(/.*)?"` then `restorecon -Rv /srv/www`. Don't `chcon` (lost on relabel) and don't disable SELinux.
- **AppArmor: confine a new daemon:** `aa-genprof /usr/bin/mydaemon` → run/exercise it → `aa-logprof` to accept
  the learned accesses → `aa-enforce`. Keep it in complain mode in staging first.
- **Least-privilege container:** `docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE --security-opt
  no-new-privileges --security-opt seccomp=default.json …`; in k8s use the Restricted PSS.

## Anti-Patterns

- **`setenforce 0` / `SELINUX=disabled` as a fix.** Disabling MAC to make an app work throws away the whole layer
  and (for SELinux) requires a full filesystem relabel to re-enable. Use `permissive` only to *diagnose*, then fix
  the label/boolean/policy.
- **Blindly piping every denial through `audit2allow -M`.** It will happily generate `allow` rules that grant far
  more than the app needs (sometimes effectively unconfining the domain). Read the rules; prefer a boolean or
  relabel first.
- **`docker run --privileged` (or k8s `privileged: true`) "to make it work."** It disables seccomp/AppArmor, grants
  all caps, and exposes host devices — a near-complete escape surface. Add the *specific* cap instead.
- **Granting `CAP_SYS_ADMIN` to a container.** It is so broad it is effectively root; many container escapes hinge
  on it.
- **Relying on AppArmor path rules where a file is reachable by multiple names** (hard links / bind mounts) — the
  rule can be bypassed via an alternate path. Use SELinux labels (inode-bound) where this matters.
- **Trying to enable both SELinux and AppArmor.** They are mutually exclusive LSMs; pick the one your distro
  defaults to. Add **BPF LSM** (stackable) if you need extra programmable enforcement alongside.
- **`chcon` for permanent SELinux labels.** It is not persisted in the fcontext db, so a relabel (`restorecon`,
  `fixfiles`, autorelabel) reverts it. Use `semanage fcontext`.

## Troubleshooting

- **App fails only with SELinux enforcing:** `setenforce 0` to confirm → `ausearch -m avc -ts recent` →
  `sealert` → apply the suggested label/boolean fix → `setenforce 1`. Re-test.
- **No AVCs but still denied:** check **dontaudit** rules are hiding them — `semodule -DB` (disable dontaudit)
  temporarily, reproduce, then `semodule -B` to restore.
- **AppArmor blocking silently:** look in `dmesg`/`journalctl -k` for `apparmor="DENIED"` lines (or `audit.log`);
  `aa-complain <profile>` to learn the needed rule, then `aa-logprof`, then `aa-enforce`.
- **Capability-related failure (`EPERM` on a privileged op despite "root"):** the cap was dropped from the
  **bounding set** or `no_new_privs`/securebits stripped it. `capsh --print` / `getpcaps <pid>` to see the live
  sets; check the systemd `CapabilityBoundingSet=`/container `--cap-drop`.
- **File cap not taking effect:** the filesystem may be mounted `nosuid` (also strips file caps) or the binary was
  copied (xattrs don't survive `cp` without `--preserve=xattr`). Re-`setcap` and check the mount options.
- **Relabel after a major mislabel:** `touch /.autorelabel && reboot` (full relabel at boot) or `restorecon -Rv /`.

## References

- LSM framework — kernel docs: https://docs.kernel.org/security/lsm.html
- Linux Security Modules overview (modules list, exclusive/stackable): https://en.wikipedia.org/wiki/Linux_Security_Modules
- LSM stacking direction — LWN: https://lwn.net/Articles/970070/
- SELinux contexts (user:role:type:level) — Red Hat: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/selinux_users_and_administrators_guide/chap-security-enhanced_linux-selinux_contexts
- Configuring the SELinux Policy (Smalley/NSA): https://www.nsa.gov/portals/75/images/resources/everyone/digital-media-center/publications/research-papers/configuring-selinux-policy-report.pdf
- SELinux MLS tutorial — Gentoo wiki: https://wiki.gentoo.org/wiki/SELinux/Tutorials/SELinux_Multi-Level_Security
- SELinux concepts — Android Open Source Project: https://source.android.com/docs/security/features/selinux/concepts
- Troubleshooting SELinux (ausearch/sealert/audit2allow) — Red Hat RHEL 9: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/troubleshooting-problems-related-to-selinux_using-selinux
- AppArmor — ArchWiki: https://wiki.archlinux.org/title/AppArmor
- Building AppArmor profiles from the command line — openSUSE: https://doc.opensuse.org/documentation/leap/security/html/book-security/cha-apparmor-commandline.html
- SELinux vs AppArmor (label vs path, distro defaults) — TuxCare: https://tuxcare.com/blog/selinux-vs-apparmor/
- AppArmor vs SELinux — apparmor.net: https://apparmor.net/about/apparmor_vs_selinux/
- capabilities(7) — man7: https://www.man7.org/linux/man-pages/man7/capabilities.7.html
- Linux Capabilities in practice — Container Solutions: https://blog.container-solutions.com/linux-capabilities-in-practice
- Docker Security Cheat Sheet — OWASP: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
- Configure a Security Context (capabilities/seLinuxOptions/seccomp) — Kubernetes: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- Linux kernel security constraints for Pods — Kubernetes: https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/
