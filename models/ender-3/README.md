# Ender 3 display mesh

Source: https://github.com/Creality3DPrinting/Ender-3/blob/master/Ender-3%20Mechanical/STP/Ender3.STEP
Copyright: Creality. License: GNU GPL v3 (included in LICENSE).

The original STEP CAD assembly was tessellated into binary STL using occt-import-js, with absolute linear deflection 0.6 mm and angular deflection 0.6 radians. This is a stock reference model, not a scan of Taylor's repaired printer. Original editable CAD source is available at the source link above.

For web delivery, coincident vertices were welded at 0.0001 mm precision and
meshoptimizer simplified the mesh to 119,990 triangles (relative error
0.000386). The STL is approximately 6 MB. Surface normals are recomputed by
the viewer. The viewer loads local Three.js 0.170.0 modules from `vendor/three/` (MIT license included).
