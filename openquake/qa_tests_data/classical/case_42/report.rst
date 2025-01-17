SAM int July 2019 A15, 300km
============================

+----------------+----------------------+
| checksum32     | 2_125_178_123        |
+----------------+----------------------+
| date           | 2022-03-17T11:23:25  |
+----------------+----------------------+
| engine_version | 3.14.0-gitaed816bf7b |
+----------------+----------------------+
| input_size     | 63_794               |
+----------------+----------------------+

num_sites = 1, num_levels = 15, num_rlzs = 1

Parameters
----------
+---------------------------------+------------------------------------------+
| parameter                       | value                                    |
+---------------------------------+------------------------------------------+
| calculation_mode                | 'preclassical'                           |
+---------------------------------+------------------------------------------+
| number_of_logic_tree_samples    | 0                                        |
+---------------------------------+------------------------------------------+
| maximum_distance                | {'default': [[2.5, 1000], [10.2, 1000]]} |
+---------------------------------+------------------------------------------+
| investigation_time              | 1.0                                      |
+---------------------------------+------------------------------------------+
| ses_per_logic_tree_path         | 1                                        |
+---------------------------------+------------------------------------------+
| truncation_level                | 3.0                                      |
+---------------------------------+------------------------------------------+
| rupture_mesh_spacing            | 20.0                                     |
+---------------------------------+------------------------------------------+
| complex_fault_mesh_spacing      | 50.0                                     |
+---------------------------------+------------------------------------------+
| width_of_mfd_bin                | 0.2                                      |
+---------------------------------+------------------------------------------+
| area_source_discretization      | None                                     |
+---------------------------------+------------------------------------------+
| pointsource_distance            | {'default': '1000'}                      |
+---------------------------------+------------------------------------------+
| ground_motion_correlation_model | None                                     |
+---------------------------------+------------------------------------------+
| minimum_intensity               | {}                                       |
+---------------------------------+------------------------------------------+
| random_seed                     | 23                                       |
+---------------------------------+------------------------------------------+
| master_seed                     | 123456789                                |
+---------------------------------+------------------------------------------+
| ses_seed                        | 42                                       |
+---------------------------------+------------------------------------------+

Input files
-----------
+-------------------------+----------------------------------+
| Name                    | File                             |
+-------------------------+----------------------------------+
| gsim_logic_tree         | `gmmLT_A15.xml <gmmLT_A15.xml>`_ |
+-------------------------+----------------------------------+
| job_ini                 | `job.ini <job.ini>`_             |
+-------------------------+----------------------------------+
| source_model_logic_tree | `ssmLT.xml <ssmLT.xml>`_         |
+-------------------------+----------------------------------+

Required parameters per tectonic region type
--------------------------------------------
+----------------------+--------------------------------+-----------+--------------+------------+
| trt_smr              | gsims                          | distances | siteparams   | ruptparams |
+----------------------+--------------------------------+-----------+--------------+------------+
| Subduction Interface | [AbrahamsonEtAl2015SInterHigh] | rrup      | backarc vs30 | mag        |
+----------------------+--------------------------------+-----------+--------------+------------+

Slowest sources
---------------
+-----------+------+-----------+-----------+--------------+
| source_id | code | calc_time | num_sites | eff_ruptures |
+-----------+------+-----------+-----------+--------------+
| int_2     | C    | 0.0       | 37        | 1_755        |
+-----------+------+-----------+-----------+--------------+

Computation times by source typology
------------------------------------
+------+-----------+-----------+--------------+--------+
| code | calc_time | num_sites | eff_ruptures | weight |
+------+-----------+-----------+--------------+--------+
| C    | 0.0       | 37        | 1_755        | 1_827  |
+------+-----------+-----------+--------------+--------+

Information about the tasks
---------------------------
+--------------------+--------+---------+--------+-----------+---------+---------+
| operation-duration | counts | mean    | stddev | min       | max     | slowfac |
+--------------------+--------+---------+--------+-----------+---------+---------+
| preclassical       | 2      | 17.2    | 99%    | 2.077E-04 | 34.4    | 1.99999 |
+--------------------+--------+---------+--------+-----------+---------+---------+
| read_source_model  | 1      | 0.04000 | nan    | 0.04000   | 0.04000 | 1.00000 |
+--------------------+--------+---------+--------+-----------+---------+---------+

Data transfer
-------------
+-------------------+------------------------------------------+----------+
| task              | sent                                     | received |
+-------------------+------------------------------------------+----------+
| read_source_model |                                          | 48.11 KB |
+-------------------+------------------------------------------+----------+
| split_task        | args=1.02 MB elements=48.2 KB func=132 B | 0 B      |
+-------------------+------------------------------------------+----------+
| preclassical      |                                          | 56.3 KB  |
+-------------------+------------------------------------------+----------+

Slowest operations
------------------
+---------------------------+----------+-----------+--------+
| calc_50526, maxmem=1.9 GB | time_sec | memory_mb | counts |
+---------------------------+----------+-----------+--------+
| total preclassical        | 34.4     | 5.67188   | 1      |
+---------------------------+----------+-----------+--------+
| weighting sources         | 17.1     | 0.0       | 37     |
+---------------------------+----------+-----------+--------+
| splitting sources         | 0.53478  | 4.19922   | 1      |
+---------------------------+----------+-----------+--------+
| importing inputs          | 0.18807  | 0.0       | 1      |
+---------------------------+----------+-----------+--------+
| composite source model    | 0.18189  | 0.0       | 1      |
+---------------------------+----------+-----------+--------+
| total read_source_model   | 0.04000  | 0.0       | 1      |
+---------------------------+----------+-----------+--------+