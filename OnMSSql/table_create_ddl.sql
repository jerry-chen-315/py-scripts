CREATE TABLE [dbo].[T_VM_EVENT](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[vm_id] [int] NULL,
	[vm_name] [nvarchar](50) NULL,
	[ip_addr] [nvarchar](50) NULL,
	[op_type] [int] NULL,
	[hd_type] [nvarchar](50) NULL,
	[old_value] [bigint] NULL,
	[new_value] [bigint] NULL,
	[event_time] [datetime] NULL,
	[comment] [nvarchar](200) NULL,
	[vdevice_id] [int] NULL,
	[update_key] [int] NULL,
	[lun_uuid] [nvarchar](255) NULL
)

CREATE TABLE [dbo].[t_log_vm_state](
	[vm_id] [int] NOT NULL,
	[vm_name] [nvarchar](50) NULL,
	[ip_addr] [nvarchar](50) NULL,
	[status] [nvarchar](50) NULL,
	[create_time] [datetime] NULL,
	[drop_time] [datetime] NULL,
	[annotation] [nvarchar](300) NULL
)