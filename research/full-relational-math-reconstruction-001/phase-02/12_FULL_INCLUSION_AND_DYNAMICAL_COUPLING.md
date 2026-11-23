# 12 — Full face-inclusion table and actual dynamics coupling boundary

## Full face order relation
The 2,187 nonempty geometric faces have 75,938 strict ordered inclusion pairs. The full list is exported in data/Q7_FACE_INCLUSION.csv. Each row records lower face, upper face, their state strings and upper dimension. Together with equality this gives 78,125=5^7 pairs. The 10,206 immediate Hasse covers are the transitive reduction and already determine the same partial order; the new CSV makes every strict relation directly inspectable.

The abstract face lattice adds one empty lower element, giving 2,188 elements and 128 additional empty-to-vertex covers. The data CSV intentionally contains only nonempty geometric faces.

Reproduce the inclusion CSV:
\`\`\`powershell
python phase-02/export_full_inclusion.py --out phase-02/data
\`\`\`

## Q7 graph in v2 is not yet a coupled dynamical network
The source projector constructs Q7 edges for rendering and computes each displayed edge stress as the arithmetic mean of the endpoint stresses. The engine's node stress, however, is assigned directly from the scalar state, an envelope based on absolute integer-index distance to gates 42/85, and an explicit phase wave. The evolution rule has no adjacency-based interaction, graph Laplacian, edge flux, neighbour coupling or graph-wave operator.

Therefore Q7 is currently a visualization/readout graph, not a dynamically coupled 128-node network. Any graph diffusion, wave propagation, coupling matrix or network bifurcation model must be built as a separately versioned research model, not retrofitted into the unchanged v2 equations.

This is a significant negative result: the existing code does not yet test dynamical emergence from Q7 topology. It tests a scalar hybrid recurrence and projects a derived node field onto the XOR graph for display.
