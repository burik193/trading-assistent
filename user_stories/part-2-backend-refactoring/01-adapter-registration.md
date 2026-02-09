# User story: Configurable or registry-based adapter registration

**Part:** 2 — Backend refactoring  
**ID:** 01-adapter-registration

---

## As a developer, I want to add or reorder data-source adapters without editing the scan service constructor, so that new data sources (e.g. Simfin, FRED) can be plugged in via configuration or a registry instead of changing core code.

## What should be done

- **Decouple adapter list from code.** The scan service currently instantiates a fixed list of adapters (e.g. Alpha Vantage, Yahoo) in `ScanService.__init__`. The set and order of adapters should be configurable—for example via a config option (e.g. list of adapter names or class names) or a registry that the scan service consults. Adding or reordering adapters should not require editing the scan service constructor.

- **Preserve current behaviour.** The existing adapters (Alpha Vantage, Yahoo Finance) should remain available and behave as today; the default configuration or registry should yield the same list and order so that existing deployments and tests continue to work.

- **Document the mechanism.** How to register a new adapter (and in what order they are tried) should be documented (e.g. in architecture.md or scan.md) so that future data sources can be added by following the same pattern.

## Why

- **Extensibility:** New data sources (e.g. from research.md or future requirements) should be added by implementing an adapter and registering it, not by modifying the scan service.
- **Environment flexibility:** Different environments might want different adapters or order (e.g. disable one provider, or try a different primary).

## Out of scope

- Changing the adapter interface (e.g. `DataSourceAdapter`); only how adapters are registered and discovered is in scope.
- Implementing new adapters (e.g. Simfin); that belongs in the “new features” part.
