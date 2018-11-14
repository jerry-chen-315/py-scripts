USE [NewVCDB]
GO

/****** Object:  Trigger [dbo].[tr_vpx_vm_config_dml]    Script Date: 09/17/2018 16:28:49 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TRIGGER [dbo].[tr_vpx_vm_config_dml]
   ON [dbo].[VPX_VM_CONFIG_INFO]
   AFTER INSERT
AS
  declare @vmid int
  declare @vmname nvarchar(50)
  
BEGIN
    -- op_type:1=update,2=insert,3=delete,4=clone,5=relocate
	-- hd_type:cpu,mem,nic,disk,disk_space,vm,ip
    SET NOCOUNT ON;
	-- when vm deleted
	IF NOT EXISTS(SELECT * FROM Deleted)
	BEGIN
	    SELECT @vmid = ID FROM Inserted;
		SELECT @vmname = NAME FROM Inserted;
		UPDATE [dbo].[T_VM_EVENT] SET vm_name = @vmname WHERE vm_id = @vmid AND vm_name = 'None' AND op_type = 2;
		UPDATE [dbo].[t_log_vm_state] SET vm_name = @vmname WHERE vm_id = @vmid AND vm_name = 'None';
	END
END
GO


