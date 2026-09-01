<div align="center">

<img src="assets/header.svg" alt="IronGap // Vault-OS — The Air-Gapped AI Appliance for Zero-Trust Environments" width="100%">

<br>

[![Company](https://img.shields.io/badge/IRONGAP-iron--gap.com-FFC93C?style=for-the-badge&labelColor=07070A)](https://www.iron-gap.com)
[![LinkedIn](https://img.shields.io/badge/LINKEDIN-taha--halakooei-FFC93C?style=for-the-badge&labelColor=07070A&logo=linkedin&logoColor=FFC93C)](https://www.linkedin.com/in/taha-halakooei)
[![Portfolio](https://img.shields.io/badge/PORTFOLIO-metronix.ir-FFC93C?style=for-the-badge&labelColor=07070A)](https://metronix.ir)
[![Email](https://img.shields.io/badge/CONTACT-taha%40iron--gap.com-FFC93C?style=for-the-badge&labelColor=07070A&logo=maildotru&logoColor=FFC93C)](mailto:taha@iron-gap.com)

</div>

---

## The premise

Every AI product being built right now assumes one thing: that you are willing to send your
data somewhere else. For most of the world that assumption is fine. For defense contractors
under CMMC, for hospitals holding genomic data, for banks running proprietary models, for
anyone operating under PIPL or a cross-border transfer regime — it is a non-starter, and no
amount of encryption-in-transit fixes it.

**I build for the people who can't say yes to that.**

Not a private cloud. Not a VPC. No network egress path at all — because a path that exists
is a path that can be exploited, and the only guarantee that survives contact with a real
adversary is the one enforced by architecture rather than policy.

<div align="center">
<img src="assets/airgap.svg" alt="Air-gap architecture — zero egress paths between the untrusted network and the Vault-OS enclave" width="100%">
</div>

---

## Vault-OS

> A hardware-tethered, fully offline AI operating system. `v1.0.9.1` · Windows shipping · Linux and macOS in development.

<details open>
<summary><b>Isolation</b> — the gap is structural, not configured</summary>
<br>

TPM 2.0 tethering binds the license to specific silicon through Platform Configuration
Registers, falling back to motherboard UUID and CPU serial. Zero-Docker by design:
PostgreSQL and pgvector run as native services, not containers, so there is no runtime to
escape and no orchestration layer to compromise. A BitLocker enclave holds the data under a
master password **IronGap does not keep a copy of** — which means a lost password is
unrecoverable data. That cuts both ways, and it is the honest cost of the guarantee.

</details>

<details>
<summary><b>Inference</b> — three engines, open weights, no API keys</summary>
<br>

A polymorphic engine layer over vLLM, Ollama and TensorRT-LLM, with multi-node GPU
clustering for distributed inference. Bundled multimodal chat, vision, embeddings and
Whisper speech recognition. Open weights only — Llama 3, Mixtral, Qwen — because a model you
cannot inspect is a dependency you cannot audit.

</details>

<details>
<summary><b>Retrieval</b> — grounded, not generated</summary>
<br>

Hybrid RAG on pgvector with HNSW indexing over 768-dimensional embeddings, with a similarity
boost for recognized entities. Automated entity and relationship extraction builds a
knowledge graph underneath, so synthesis is anchored to retrieved facts. A multi-agent
critic runs an adversarial second pass before any output is accepted.

</details>

<details>
<summary><b>Agency</b> — 33 node types, sandboxed</summary>
<br>

A DAG workflow runtime with Kahn topological sorting, 33 node types, 33 contextual assistant
tools, and sandboxed ReAct agents. Autonomous execution inside a perimeter that has no way
to reach out of itself.

</details>

<details>
<summary><b>Custody</b> — 9 clearance tiers and a burn switch</summary>
<br>

A 9-tier RBAC matrix with multi-party encrypted messaging, per-member restrictions and
server-enforced auto-delete. SHA-256 hash-chained, RSA-signed audit logs. A NIST SP 800-88
burn protocol for cryptographic self-termination. Resumable ~22GB unpack that survives power
loss, and a shutdown path that *verifies* the enclave locked rather than assuming it did.

</details>

<div align="center">
<br>
<img src="assets/ledger.svg" alt="Tamper-evident audit ledger — SHA-256 chained, RSA signed" width="100%">
</div>

---

## The ethic

Security work is unusually easy to fake. You can ship a product that says "military-grade"
and "zero-trust" on the box and never once be held to it, because the failure mode is
silent — nobody finds out the guarantee was hollow until an adversary does, and by then the
data is gone.

So I try to build things that are **falsifiable**. A hash chain either verifies or it
doesn't. An egress count is either zero or it isn't. A burn protocol either meets NIST
SP 800-88 or it doesn't. Claims that can be checked are worth more than claims that sound
impressive, and I would rather ship a smaller promise I can prove than a larger one I can't.

The password we can't recover is the clearest case. It would be trivial to keep an escrow
copy and quietly call it a support feature. We don't, because sovereignty with a vendor
backdoor is not sovereignty — it is a marketing claim with an asterisk.

---

## Other work

<table>
<tr>
<td width="50%" valign="top">

### [TRACES](https://github.com/taha-halakoo/Lumo-traces)
Location-aware social platform. Content is pinned to physical coordinates and stays locked
until you are within 20 m of it.

`Fastify` `PostGIS` `pgvector` `Flutter`

Hybrid vector + spatial ranking, offline-first mobile architecture, realtime sync, in a
Turborepo monorepo.

</td>
<td width="50%" valign="top">

### [StudyHub OS](https://github.com/taha-halakoo/studyhub)
Modular productivity dashboard with an integrated AI assistant.

`React` `TypeScript` `Supabase` `Zustand`

Lazy-loaded feature modules, RBAC over Supabase Auth, realtime collaboration.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### [Virtual Mouse](https://github.com/taha-halakoo/virtual-mouse)
Hands-free pointer control from hand tracking.

`Python` `MediaPipe` `OpenCV`

One-Euro filtering with relative delta tracking — the air becomes a trackpad, with a clutch
gesture and a precision mode.

</td>
<td width="50%" valign="top">

### YTU BME Nexus
Department platform for Biomedical Engineering at Yıldız Technical University.

`React` `Supabase`

Built for the department I study in.

</td>
</tr>
</table>

---

## Stack

<div align="center">

![C++](https://img.shields.io/badge/C++-07070A?style=for-the-badge&logo=cplusplus&logoColor=FFC93C)
![Python](https://img.shields.io/badge/Python-07070A?style=for-the-badge&logo=python&logoColor=FFC93C)
![TypeScript](https://img.shields.io/badge/TypeScript-07070A?style=for-the-badge&logo=typescript&logoColor=FFC93C)
![Node.js](https://img.shields.io/badge/Node.js-07070A?style=for-the-badge&logo=nodedotjs&logoColor=FFC93C)
![Dart](https://img.shields.io/badge/Dart-07070A?style=for-the-badge&logo=dart&logoColor=FFC93C)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-07070A?style=for-the-badge&logo=postgresql&logoColor=FFC93C)
![Flutter](https://img.shields.io/badge/Flutter-07070A?style=for-the-badge&logo=flutter&logoColor=FFC93C)
![React](https://img.shields.io/badge/React-07070A?style=for-the-badge&logo=react&logoColor=FFC93C)
![NVIDIA](https://img.shields.io/badge/TensorRT--LLM-07070A?style=for-the-badge&logo=nvidia&logoColor=FFC93C)
![Linux](https://img.shields.io/badge/Linux-07070A?style=for-the-badge&logo=linux&logoColor=FFC93C)

**Security** `TPM 2.0` · `HSM` · `bare-metal architecture` · `applied cryptography` · `zero-trust design` · `NIST SP 800-88`
**AI** `RAG pipelines` · `pgvector / HNSW` · `knowledge graphs` · `DAG orchestration` · `ReAct agents` · `MCP`
**Engineering** `MATLAB` · `Simulink` · `embedded systems` · `system architecture`

</div>

---

## Signal

<div align="center">

<img src="assets/stats.svg" alt="GitHub activity — commits, private share, repositories, stars and language distribution" width="100%">

<sub>Generated daily by <a href="scripts/gen_stats.py">a script in this repo</a> rather than a third-party widget —
the usual ones rate-limit, run out of quota, and eventually stop rendering.
Fitting, for someone who builds things that don't phone home.</sub>

</div>

---

<div align="center">

### Elsewhere

Founder & Chief Architect at **[IronGap Technologies](https://www.iron-gap.com)** · Istanbul, Türkiye
Biomedical Engineering at **Yıldız Technical University** · MATE R&D, Polaris Group

[iron-gap.com](https://www.iron-gap.com) · [LinkedIn](https://www.linkedin.com/in/taha-halakooei) · [Company](https://www.linkedin.com/company/irongap-technologies) · [taha@iron-gap.com](mailto:taha@iron-gap.com)

<br>

<sub><i>Absolute data sovereignty requires absolute isolation.</i></sub>

</div>
