---
title: "Distributed Systems & Consensus (theory + blockchain mechanisms)"
description: "Distributed systems and consensus theory plus blockchain consensus mechanisms — the fundamental problem of agreement across unreliable nodes. Owns both the classical/crash-fault side and the Byzantine"
---

Distributed systems and consensus theory plus blockchain consensus mechanisms — the fundamental problem of agreement across unreliable nodes. Owns both the classical/crash-fault side and the Byzantine/blockchain side.

Foundations: CAP theorem and PACELC extension, FLP impossibility, linearizability vs sequential vs causal vs eventual consistency, Lamport clocks and vector clocks, state-machine replication, quorum intersection, crash-stop vs crash-recover vs Byzantine failure models, safety vs liveness properties.

Crash-fault consensus: Paxos and Multi-Paxos, Raft (leader election, log replication, safety proofs), Viewstamped Replication, Zab (Zookeeper), gossip/epidemic protocols, CRDTs for AP systems.

Byzantine consensus: PBFT (three-phase, 3f+1 quorum), Tendermint/CometBFT, HotStuff (linear communication), threshold cryptography.

Blockchain consensus: Nakamoto longest-chain PoW, Proof of Stake mechanics, Ethereum's Gasper (Casper FFG finality + LMD-GHOST fork-choice), Cardano Ouroboros, Solana Tower BFT, fork-choice rules, finality vs probabilistic settlement, Sybil resistance, the scalability/security/decentralization trilemma, long-range attacks, nothing-at-stake, selfish mining.
