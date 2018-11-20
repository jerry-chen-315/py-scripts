# py-scripts
日常运维python脚本                                                                                                                  
**jmx_to_es**：采集java jmx性能数据值elasticsearch。从parfile参数文件读取配置信息。                       
**mycheck_oracle.py**:Nagios监控oracle数据库脚本。

**vcenter_vm_event目录说明**：vcenter虚拟机事件结合ELK。目前功能可用于记录虚拟机硬件(CPU,MEM,DISK,NIC)新增、删除、变更，虚拟机迁移、重启、关机事件。
                        etl_to_kafka脚本用于从vcenter数据库抽取数据至kafka
                        目录OnMSSql是基于sqlserver环境的数据库脚本
                        目录OnPostgresql是基于vcsa环境的数据库脚本
