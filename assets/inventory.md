# Asset inventory

| id | category | size W x H x D (m) | tris | ports |
|---|---|---|---|---|
| `control_cabinet` | control | 1.00 x 1.88 x 0.62 | 1206 | `power_in`, `signal` |
| `operator_console` | control | 1.38 x 1.38 x 0.75 | 840 | `power`, `data` |
| `air_receiver` | fluids | 1.12 x 2.25 x 1.12 | 3442 | `in`, `out` |
| `boiler` | fluids | 1.75 x 3.12 x 1.78 | 7794 | `water_in`, `steam_out`, `fuel` |
| `compressor` | fluids | 2.00 x 1.62 x 1.38 | 2764 | `in`, `air_out`, `power` |
| `cooling_chiller` | fluids | 2.00 x 1.31 x 1.50 | 2322 | `water_in`, `water_out`, `power` |
| `pump` | fluids | 1.88 x 1.81 x 1.16 | 4258 | `suction`, `discharge`, `power` |
| `conveyor_corner` | logistics | 1.75 x 0.94 x 2.03 | 2460 | `in`, `out` |
| `conveyor_diverter` | logistics | 2.00 x 1.25 x 1.00 | 2418 | `in`, `out`, `reject`, `air`, `power` |
| `conveyor_endstop` | logistics | 1.44 x 1.03 x 1.00 | 1096 | `in`, `chute` |
| `conveyor_gate` | logistics | 1.44 x 1.25 x 1.00 | 1678 | `in`, `out`, `air` |
| `conveyor_hopper` | logistics | 1.78 x 1.56 x 1.50 | 980 | `in`, `out` |
| `conveyor_merge` | logistics | 2.00 x 1.25 x 2.00 | 2680 | `in_main`, `in_side`, `out`, `air`, `power` |
| `conveyor_scanner` | logistics | 2.00 x 2.91 x 1.03 | 2498 | `in`, `out`, `scan`, `power` |
| `conveyor_straight` | logistics | 2.00 x 0.94 x 1.00 | 1944 | `in`, `out`, `power` |
| `pipe_elbow` | logistics | 1.44 x 1.44 x 2.00 | 3660 | `a`, `b` |
| `pipe_straight` | logistics | 2.00 x 1.44 x 0.94 | 2610 | `a`, `b` |
| `pipe_tee` | logistics | 2.00 x 1.88 x 0.94 | 2072 | `a`, `b`, `branch` |
| `valve` | logistics | 2.00 x 1.62 x 0.94 | 2414 | `a`, `b` |
| `generator` | power | 2.50 x 2.25 x 1.50 | 2450 | `power_out`, `exhaust`, `fuel` |
| `motor` | power | 2.06 x 1.78 x 1.25 | 5920 | `shaft`, `power` |
| `power_transformer` | power | 1.50 x 1.81 x 1.50 | 2594 | `hv_in`, `lv_out` |
| `assembler` | process | 2.00 x 2.00 x 2.00 | 2888 | `in`, `out`, `power`, `coolant` |
| `hydraulic_press` | process | 1.50 x 3.19 x 1.50 | 2530 | `in`, `out`, `power`, `hydraulic` |
| `smelter_furnace` | process | 2.00 x 3.06 x 2.00 | 5122 | `charge`, `tap`, `exhaust` |
| `barrel` | props | 0.62 x 1.12 x 0.62 | 1650 | `in` |
| `cardboard_boxes` | props | 1.00 x 0.62 x 1.00 | 674 | - |
| `crate` | props | 1.00 x 0.81 x 1.00 | 1322 | - |
| `pallet` | props | 1.00 x 0.28 x 1.00 | 816 | - |
| `agv` | robotics | 1.47 x 0.75 x 1.00 | 1182 | `deck`, `power` |
| `robot_arm` | robotics | 1.50 x 2.81 x 1.50 | 4032 | `grasp`, `power` |
| `safety_fence` | safety | 2.06 x 1.75 x 0.19 | 1468 | `hinge` |
| `gas_tank` | storage | 3.00 x 2.00 x 1.62 | 7664 | `in`, `out`, `drain` |
| `silo` | storage | 2.00 x 3.31 x 2.00 | 9154 | `in`, `out` |
| `storage_rack` | storage | 2.00 x 3.09 x 1.00 | 2288 | `slot_a`, `slot_b` |
| `water_tank` | storage | 2.00 x 3.00 x 2.00 | 8746 | `in`, `out`, `vent` |

Total: 36 assets, 109636 triangles, 8.8 MB of GLB.
