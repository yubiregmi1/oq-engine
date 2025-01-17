late_weights sampling
=====================

+----------------+----------------------+
| checksum32     | 477_914_009          |
+----------------+----------------------+
| date           | 2022-03-17T11:24:21  |
+----------------+----------------------+
| engine_version | 3.14.0-gitaed816bf7b |
+----------------+----------------------+
| input_size     | 3_421                |
+----------------+----------------------+

num_sites = 1, num_levels = 20, num_rlzs = 10

Parameters
----------
+---------------------------------+--------------------------------------------+
| parameter                       | value                                      |
+---------------------------------+--------------------------------------------+
| calculation_mode                | 'preclassical'                             |
+---------------------------------+--------------------------------------------+
| number_of_logic_tree_samples    | 10                                         |
+---------------------------------+--------------------------------------------+
| maximum_distance                | {'default': [[2.5, 200.0], [10.2, 200.0]]} |
+---------------------------------+--------------------------------------------+
| investigation_time              | 1.0                                        |
+---------------------------------+--------------------------------------------+
| ses_per_logic_tree_path         | 1                                          |
+---------------------------------+--------------------------------------------+
| truncation_level                | 2.0                                        |
+---------------------------------+--------------------------------------------+
| rupture_mesh_spacing            | 1.0                                        |
+---------------------------------+--------------------------------------------+
| complex_fault_mesh_spacing      | 1.0                                        |
+---------------------------------+--------------------------------------------+
| width_of_mfd_bin                | 1.0                                        |
+---------------------------------+--------------------------------------------+
| area_source_discretization      | None                                       |
+---------------------------------+--------------------------------------------+
| pointsource_distance            | {'default': '1000'}                        |
+---------------------------------+--------------------------------------------+
| ground_motion_correlation_model | None                                       |
+---------------------------------+--------------------------------------------+
| minimum_intensity               | {}                                         |
+---------------------------------+--------------------------------------------+
| random_seed                     | 1067                                       |
+---------------------------------+--------------------------------------------+
| master_seed                     | 123456789                                  |
+---------------------------------+--------------------------------------------+
| ses_seed                        | 42                                         |
+---------------------------------+--------------------------------------------+

Input files
-----------
+-------------------------+--------------------------------------------------------------+
| Name                    | File                                                         |
+-------------------------+--------------------------------------------------------------+
| gsim_logic_tree         | `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                 |
+-------------------------+--------------------------------------------------------------+
| job_ini                 | `job.ini <job.ini>`_                                         |
+-------------------------+--------------------------------------------------------------+
| source_model_logic_tree | `source_model_logic_tree.xml <source_model_logic_tree.xml>`_ |
+-------------------------+--------------------------------------------------------------+

Required parameters per tectonic region type
--------------------------------------------
+----------------------+------------------------------------+-----------+------------+------------+
| trt_smr              | gsims                              | distances | siteparams | ruptparams |
+----------------------+------------------------------------+-----------+------------+------------+
| active shallow crust | [AkkarBommer2010] [SadighEtAl1997] | rjb rrup  | vs30       | mag rake   |
+----------------------+------------------------------------+-----------+------------+------------+

Slowest sources
---------------
+-----------+------+-----------+-----------+--------------+
| source_id | code | calc_time | num_sites | eff_ruptures |
+-----------+------+-----------+-----------+--------------+
| 1         | P    | 0.0       | 1         | 3            |
+-----------+------+-----------+-----------+--------------+

Computation times by source typology
------------------------------------
+------+-----------+-----------+--------------+---------+
| code | calc_time | num_sites | eff_ruptures | weight  |
+------+-----------+-----------+--------------+---------+
| P    | 0.0       | 1         | 3            | 4.06000 |
+------+-----------+-----------+--------------+---------+

Information about the tasks
---------------------------
+--------------------+--------+---------+--------+---------+---------+---------+
| operation-duration | counts | mean    | stddev | min     | max     | slowfac |
+--------------------+--------+---------+--------+---------+---------+---------+
| preclassical       | 1      | 0.00200 | nan    | 0.00200 | 0.00200 | 1.00000 |
+--------------------+--------+---------+--------+---------+---------+---------+
| read_source_model  | 1      | 0.06532 | nan    | 0.06532 | 0.06532 | 1.00000 |
+--------------------+--------+---------+--------+---------+---------+---------+

Data transfer
-------------
+-------------------+-------------------------------------------+----------+
| task              | sent                                      | received |
+-------------------+-------------------------------------------+----------+
| read_source_model |                                           | 1.55 KB  |
+-------------------+-------------------------------------------+----------+
| split_task        | args=520.13 KB elements=1.27 KB func=66 B | 0 B      |
+-------------------+-------------------------------------------+----------+
| preclassical      |                                           | 1.33 KB  |
+-------------------+-------------------------------------------+----------+

Slowest operations
------------------
+---------------------------+-----------+-----------+--------+
| calc_50537, maxmem=1.9 GB | time_sec  | memory_mb | counts |
+---------------------------+-----------+-----------+--------+
| importing inputs          | 0.12342   | 0.0       | 1      |
+---------------------------+-----------+-----------+--------+
| composite source model    | 0.11224   | 0.0       | 1      |
+---------------------------+-----------+-----------+--------+
| total read_source_model   | 0.06532   | 0.0       | 1      |
+---------------------------+-----------+-----------+--------+
| total preclassical        | 0.00200   | 0.0       | 1      |
+---------------------------+-----------+-----------+--------+
| weighting sources         | 0.00120   | 0.0       | 1      |
+---------------------------+-----------+-----------+--------+
| splitting sources         | 3.257E-04 | 0.0       | 1      |
+---------------------------+-----------+-----------+--------+