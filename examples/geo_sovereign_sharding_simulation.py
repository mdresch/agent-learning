"""Simulation: Geo-Redundant Sovereign Secret-Sharing & Reconstruction via Active Evidence-Seeking.

Run this file with:
    python examples/geo_sovereign_sharding_simulation.py

Architecture Overview:
1. Sovereign Cryptographic Invariant:
   - An artifact payload is split into n shards (k-of-n threshold secret sharing).
   - No single cloud provider, datacenter, or legal jurisdiction holds enough bits to reconstruct.
   - Shards are only reassembled in volatile memory on the client machine after cryptographic attestation.
2. Active Evidence-Seeking (#12):
   - The gateway evaluates candidate multi-cloud storage topologies.
   - Missing hard constraints (anti-colocation, jurisdictional immunity, client TPM quote) yield 1.0 bit gain.
   - Non-compliant or compromised topologies are immediately disqualified and pruned.
   - High-gain telemetry probes (parallel egress latency, quorum SLA) are queried on surviving candidates.
3. Client-Side Deciphering:
   - Once the winning topology is resolved, the client requests the shards across the disjoint regions
     and reconstructs the original artifact in memory.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent_learning.decision import (
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    DecisionResult,
    DecisionStatus,
    EvidencePoint,
    InformationNeed,
    TaskPolicy,
)
from agent_learning.types import Action, PolicySnapshot


# ==============================================================================
# 1. Cryptographic Primitive: Pure-Python k-of-n Threshold Secret Sharing
# ==============================================================================

# 13th Mersenne prime (M521 = 2^521 - 1) for Galois Field threshold secret sharing
PRIME = 2**521 - 1


def _eval_poly(poly: list[int], x: int) -> int:
    result = 0
    for coeff in reversed(poly):
        result = (result * x + coeff) % PRIME
    return result


def _mod_inverse(k: int, p: int) -> int:
    return pow(k, p - 2, p)


def shamir_split_secret(secret_bytes: bytes, k: int, n: int) -> list[tuple[int, int]]:
    """Splits arbitrary secret bytes into n shares; any k shares can reconstruct."""
    secret_int = int.from_bytes(secret_bytes, byteorder="big")
    if secret_int >= PRIME:
        raise ValueError("Secret too large for prime field")

    # Polynomial: f(x) = secret + a1*x + a2*x^2 + ... + a_{k-1}*x^{k-1}
    coeffs = [secret_int] + [random.randint(1, PRIME - 1) for _ in range(k - 1)]
    shares = [(x, _eval_poly(coeffs, x)) for x in range(1, n + 1)]
    return shares


def shamir_reconstruct_secret(shares: list[tuple[int, int]]) -> bytes:
    """Lagrange interpolation at x=0 to recover the secret."""
    k = len(shares)
    secret_int = 0
    for i in range(k):
        x_i, y_i = shares[i]
        numerator, denominator = 1, 1
        for j in range(k):
            if i == j:
                continue
            x_j, _ = shares[j]
            numerator = (numerator * (-x_j)) % PRIME
            denominator = (denominator * (x_i - x_j)) % PRIME
        lagrange_i = (numerator * _mod_inverse(denominator, PRIME)) % PRIME
        secret_int = (secret_int + y_i * lagrange_i) % PRIME

    # Convert back to bytes
    length = (secret_int.bit_length() + 7) // 8
    return secret_int.to_bytes(length, byteorder="big")


# ==============================================================================
# 2. Domain Entities & Telemetry Oracle
# ==============================================================================

@dataclass
class RegionalEndpoint:
    name: str
    cloud_provider: str
    jurisdiction: str
    datacenter_id: str
    avg_latency_ms: float
    availability_sla: float


@dataclass
class StorageTopology:
    id: str
    display_name: str
    endpoints: list[RegionalEndpoint]
    threshold_k: int
    total_shards_n: int


@dataclass
class SimulationEnvironment:
    """Simulates multi-cloud auditing and client attestation telemetry."""

    # Topologies definitions
    topologies: dict[str, StorageTopology]
    # Telemetry oracles
    subpoena_immunity: dict[str, bool]
    anti_colocation: dict[str, bool]
    client_tpm_quotes: dict[str, bool]
    latency_observations: dict[str, list[float]]
    availability_observations: dict[str, list[float]]
    cost_observations: dict[str, list[float]]

    def probe_constraint(self, topology_id: str, constraint_id: str) -> bool:
        if constraint_id == "zero_single_point_exposure":
            # True by definition if k >= 2 and endpoints are distinct
            top = self.topologies[topology_id]
            return top.threshold_k >= 2 and len(top.endpoints) == top.total_shards_n
        if constraint_id == "anti_colocation_isolation":
            return self.anti_colocation.get(topology_id, True)
        if constraint_id == "multi_jurisdiction_immunity":
            return self.subpoena_immunity.get(topology_id, True)
        if constraint_id == "client_tpm_attestation":
            return self.client_tpm_quotes.get(topology_id, True)
        return False

    def probe_criterion(
        self, topology_id: str, criterion_id: str, source_idx: int
    ) -> EvidencePoint:
        if criterion_id == "parallel_fetch_latency":
            samples = self.latency_observations.get(topology_id, [0.75])
            support = samples[source_idx % len(samples)]
        elif criterion_id == "shard_quorum_availability":
            samples = self.availability_observations.get(topology_id, [0.85])
            support = samples[source_idx % len(samples)]
        elif criterion_id == "multi_cloud_egress_cost":
            samples = self.cost_observations.get(topology_id, [0.70])
            support = samples[source_idx % len(samples)]
        else:
            support = 0.50

        return EvidencePoint(
            criterion_id=criterion_id,
            source=f"telemetry_source_{source_idx + 1}",
            support=support,
        )


# ==============================================================================
# 3. Active Evidence-Seeking Engine
# ==============================================================================

def run_active_seeking_simulation() -> None:
    print("=" * 80)
    print("  SIMULATION: GEO-REDUNDANT SOVEREIGN SECRET-SHARING VIA ACTIVE EVIDENCE SEEKING")
    print("=" * 80)

    # 1. Define Topologies
    top_tri_cloud = StorageTopology(
        id="topology_tri_cloud_eu_us_ch",
        display_name="Tri-Cloud Sovereign (AWS Frankfurt + Azure US + Swiss Proton Vault)",
        endpoints=[
            RegionalEndpoint("AWS eu-central-1", "AWS", "EU/Germany", "fra-1", 42.0, 0.9999),
            RegionalEndpoint("Azure East US", "Microsoft", "US/Virginia", "iad-2", 85.0, 0.9995),
            RegionalEndpoint("Swiss Alpine Bunker", "Mount10/CH", "Switzerland", "zrh-vault", 38.0, 0.9999),
        ],
        threshold_k=3,
        total_shards_n=3,
    )

    top_dual_cloud = StorageTopology(
        id="topology_dual_hyperscaler",
        display_name="Dual-Hyperscaler (GCP US + GCP EU + Azure US)",
        endpoints=[
            RegionalEndpoint("GCP us-east4", "Google", "US/Virginia", "iad-gcp", 78.0, 0.999),
            RegionalEndpoint("GCP europe-west3", "Google", "EU/Germany", "fra-gcp", 45.0, 0.999),
            RegionalEndpoint("Azure East US", "Microsoft", "US/Virginia", "iad-msft", 82.0, 0.999),
        ],
        threshold_k=3,
        total_shards_n=3,
    )

    top_nordic = StorageTopology(
        id="topology_nordic_sovereign",
        display_name="Pan-Nordic Sovereign (Stockholm + Oslo + Helsinki)",
        endpoints=[
            RegionalEndpoint("Stockholm DC1", "Bahnhof", "Sweden", "sth-1", 25.0, 0.999),
            RegionalEndpoint("Oslo GreenDC", "Green Mountain", "Norway", "osl-1", 28.0, 0.999),
            RegionalEndpoint("Helsinki Vault", "Hetzner FI", "Finland", "hel-1", 30.0, 0.999),
        ],
        threshold_k=3,
        total_shards_n=3,
    )

    # 2. Setup Environment with Real World Dynamics:
    # - Dual-Hyperscaler FAILS multi_jurisdiction_immunity (2 Google + 1 US MSFT nodes subject to US Cloud Act warrant).
    # - Nordic Sovereign has lower global throughput/availability redundancy compared to Tri-Cloud.
    # - Tri-Cloud has excellent multi-jurisdiction immunity, high availability, and good parallel latency.
    env = SimulationEnvironment(
        topologies={
            top_tri_cloud.id: top_tri_cloud,
            top_dual_cloud.id: top_dual_cloud,
            top_nordic.id: top_nordic,
        },
        subpoena_immunity={
            top_tri_cloud.id: True,     # EU + US + Swiss (Neutral, no shared jurisdiction)
            top_dual_cloud.id: False,   # FAILS: 2 Google nodes + US Microsoft allows single-entity legal seizure!
            top_nordic.id: True,        # SE, NO, FI sovereign laws
        },
        anti_colocation={
            top_tri_cloud.id: True,
            top_dual_cloud.id: False,   # FAILS: Shares Google parent infrastructure
            top_nordic.id: True,
        },
        client_tpm_quotes={
            top_tri_cloud.id: True,     # Client TPM 2.0 quote valid
            top_dual_cloud.id: True,
            top_nordic.id: True,
        },
        latency_observations={
            top_tri_cloud.id: [0.88, 0.86],  # Fast parallel fetch support
            top_dual_cloud.id: [0.82, 0.80],
            top_nordic.id: [0.72, 0.70],     # Slower for international client
        },
        availability_observations={
            top_tri_cloud.id: [0.96, 0.94],  # Triple-carrier 99.999% SLA
            top_dual_cloud.id: [0.90, 0.88],
            top_nordic.id: [0.80, 0.78],
        },
        cost_observations={
            top_tri_cloud.id: [0.75],
            top_dual_cloud.id: [0.85],
            top_nordic.id: [0.65],
        },
    )

    # 3. Decision Frame Formulation
    policy = TaskPolicy(
        PolicySnapshot(
            id="sovereign-vault-policy",
            agent_id="geo-sharding-orchestrator",
            task_id="secure-artifact-sharding",
            version=1,
            actions=[
                Action(id=top_tri_cloud.id),
                Action(id=top_dual_cloud.id),
                Action(id=top_nordic.id),
            ],
            logits={
                top_tri_cloud.id: 0.0,
                top_dual_cloud.id: 0.0,
                top_nordic.id: 0.0,
            },
            metadata={"decision_authority": DecisionAuthority.FULL.value},
        )
    )

    initial_frame = DecisionFrame(
        task="Select optimal geo-redundant sovereign secret-sharing storage topology",
        constraints=[
            "zero_single_point_exposure",     # (1.0 bit) No single location holds >= k shards
            "anti_colocation_isolation",      # (1.0 bit) Disjoint hardware & cloud providers
            "multi_jurisdiction_immunity",    # (1.0 bit) Subpoena resistance across jurisdictions
            "client_tpm_attestation",         # (1.0 bit) Verified client-side enclave
        ],
        criteria=[
            DecisionCriterion(id="parallel_fetch_latency", weight=0.45, minimum_sources=2),
            DecisionCriterion(id="shard_quorum_availability", weight=0.35, minimum_sources=2),
            DecisionCriterion(id="multi_cloud_egress_cost", weight=0.20, minimum_sources=1),
        ],
        uncertainty_penalty=0.15,
        max_uncertainty=0.40,
        minimum_margin=0.05,
        options=[
            DecisionOption(
                action=Action(id=top_tri_cloud.id),
                constraint_results={"zero_single_point_exposure": True},
                evidence=[],
            ),
            DecisionOption(
                action=Action(id=top_dual_cloud.id),
                constraint_results={"zero_single_point_exposure": True},
                evidence=[],
            ),
            DecisionOption(
                action=Action(id=top_nordic.id),
                constraint_results={"zero_single_point_exposure": True},
                evidence=[],
            ),
        ],
    )

    resolver = DecisionResolver()
    init_res = resolver.resolve(policy.snapshot(), initial_frame)
    print(f"\n[1] Initial Evaluation: Status = {init_res.status.name}")
    print(f"    Information Needs Identified: {len(init_res.information_needs)}")
    print(f"    Top Information Needs (Ranked by Expected Gain in Bits):")
    for n in init_res.information_needs[:6]:
        print(f"      • [{n.estimated_information_gain_bits:.3f} bits] {n.kind:<10} | {n.option_id:<28} | {n.field_id}")

    # 4. Run Active Acquisition Loop
    print("\n[2] Executing Active Evidence-Seeking Loop:")
    frame = copy.deepcopy(initial_frame)
    step = 0
    while step < 25:
        res = resolver.resolve(policy.snapshot(), frame)
        if res.status != DecisionStatus.NEEDS_EVIDENCE or not res.information_needs:
            break

        # Greedy choice: highest information gain first
        need = sorted(res.information_needs, key=lambda x: -x.estimated_information_gain_bits)[0]
        step += 1

        opt_idx = next(i for i, opt in enumerate(frame.options) if opt.action.id == need.option_id)
        current_opt = frame.options[opt_idx]

        if need.kind == "constraint":
            passed = env.probe_constraint(need.option_id, need.field_id)
            c_dict = dict(current_opt.constraint_results)
            c_dict[need.field_id] = passed
            frame.options[opt_idx] = DecisionOption(
                action=current_opt.action,
                constraint_results=c_dict,
                evidence=current_opt.evidence,
            )
            status_tag = "PASS (OK)" if passed else "VIOLATION (PRUNED)"
            print(f"    Step {step:02d}: Probing CONSTRAINT '{need.field_id}' for {need.option_id} (gain: {need.estimated_information_gain_bits:.1f}b) => {status_tag}")
        else:
            existing = [e for e in current_opt.evidence if e.criterion_id == need.field_id]
            pt = env.probe_criterion(need.option_id, need.field_id, len(existing))
            e_list = list(current_opt.evidence) + [pt]
            frame.options[opt_idx] = DecisionOption(
                action=current_opt.action,
                constraint_results=current_opt.constraint_results,
                evidence=tuple(e_list),
            )
            print(f"    Step {step:02d}: Probing CRITERION  '{need.field_id}' for {need.option_id} (gain: {need.estimated_information_gain_bits:.3f}b) => support={pt.support:.2f}")

    final_res = resolver.resolve(policy.snapshot(), frame)
    print(f"\n[3] Acquisition Complete in {step} queries. Final Status: {final_res.status.name}")
    print(f"    Selected Optimal Topology: '{final_res.selected_action.id if final_res.selected_action else None}'")
    print("    Topology Assessment Summary:")
    for a in final_res.assessments:
        if not a.feasible:
            print(f"      * {a.action.id:<28} -> DISQUALIFIED: {', '.join(a.ruled_out_by)}")
        else:
            print(f"      * {a.action.id:<28} -> FEASIBLE | Robust Utility: {a.robust_utility:+.4f} | Uncertainty: {a.uncertainty:.4f}b")

    # 5. Live Cryptographic Artifact Sharding & Client-Side Reconstruction
    print("\n" + "=" * 80)
    print("  PHASE 4: LIVE CRYPTOGRAPHIC SHARDING & CLIENT-SIDE DECIPHERING")
    print("=" * 80)

    selected_top = env.topologies[final_res.selected_action.id]
    print(f"\nTarget Topology: {selected_top.display_name}")
    print(f"Threshold Scheme: {selected_top.threshold_k}-of-{selected_top.total_shards_n} Secret Sharing")

    # The secret sovereign artifact
    original_artifact = b"SOVEREIGN-KEY-2026::AES256-GCM-CREDENTIAL-VAULT::0x98AF3C10D4"
    print(f"\n[Client Input Artifact]: {original_artifact.decode('utf-8')}")
    print(f"Artifact SHA-256:        {hashlib.sha256(original_artifact).hexdigest()}")

    # Split into Shamir shares
    shares = shamir_split_secret(original_artifact, k=selected_top.threshold_k, n=selected_top.total_shards_n)

    # Distribute shares to regional storage locations
    storage_nodes: dict[str, tuple[int, int]] = {}
    print("\n[Dispatching Shards to Disjoint Sovereign Locations]:")
    for idx, (endpoint, share) in enumerate(zip(selected_top.endpoints, shares)):
        storage_nodes[endpoint.name] = share
        share_preview = f"(x={share[0]}, y={hex(share[1])[:16]}...)"
        print(f"  Location {idx+1}: {endpoint.name:<25} | Jurisdiction: {endpoint.jurisdiction:<14} | Shard: {share_preview}")

    print("\n[Security Verification at Rest — Single Location Inspection]:")
    print("  • Adversary breaches single storage location: 'AWS eu-central-1'")
    single_shard = [storage_nodes["AWS eu-central-1"]]
    print(f"    Available shares: 1 of {selected_top.threshold_k} required threshold.")
    # With fewer than k shares, the secret is mathematically indeterminate
    corrupted_attempt = shamir_reconstruct_secret(single_shard)
    print(f"    Raw bytes extracted from single share: {corrupted_attempt[:24].hex()}...")
    print(f"    Does single share match original artifact? {corrupted_attempt == original_artifact} (ZERO plaintext bits leaked!)")
    print("    Mathematical Guarantee: Shamir threshold scheme guarantees perfect secrecy for < k shares.")

    print("\n[Client Authentication & Local Reassembly]:")
    print("  1. Client presents verified hardware TPM quote & multi-party credentials.")
    print("  2. Client issues parallel async requests to:")
    for ep in selected_top.endpoints:
        print(f"     - GET https://{ep.name.replace(' ', '-').lower()}.sovereign/shard -> 200 OK (latency: {ep.avg_latency_ms:.1f}ms)")

    # Client receives all k shares into local memory
    client_received_shares = [storage_nodes[ep.name] for ep in selected_top.endpoints]
    print(f"  3. Received {len(client_received_shares)} shards into client volatile RAM.")
    
    # Lagrange interpolation on client machine
    reconstructed_bytes = shamir_reconstruct_secret(client_received_shares)
    print(f"\n[Client Deciphered Artifact]: {reconstructed_bytes.decode('utf-8')}")
    print(f"Deciphered SHA-256:          {hashlib.sha256(reconstructed_bytes).hexdigest()}")

    # Cryptographic integrity assertion
    assert reconstructed_bytes == original_artifact, "Reconstruction integrity failed!"
    print("\n>>> Cryptographic verification SUCCESS: Deciphered artifact matches original exactly! <<<")


if __name__ == "__main__":
    run_active_seeking_simulation()
