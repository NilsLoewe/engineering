<!-- Erzeugt von tools/build_katalog.py aus katalog/. Nicht von Hand ändern. -->
# Lens: Design and code smells

- When a `case`/`switch` or `is_a?` on the same type or kind appears a second time, move the variation into one lookup map or polymorphic type. (severity: major) `[design-no-repeated-type-switch]`
- Define each domain fact (limit, state list, mapping, format) once per repo and reference it; never copy its literal into a second file. (severity: major) `[design-one-home-per-fact]`
- Do not store a value that can be computed from other state (column, instance variable, `useState`); compute it where it is read. (severity: major) `[design-derive-dont-store]`
