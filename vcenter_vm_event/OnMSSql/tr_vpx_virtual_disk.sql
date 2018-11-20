USE [NewVCDB]
GO

/****** Object:  Trigger [dbo].[tr_vpx_virtual_disk]    Script Date: 09/17/2018 16:29:54 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TRIGGER [dbo].[tr_vpx_virtual_disk]
   ON [dbo].[VPX_VIRTUAL_DISK]
   AFTER INSERT, UPDATE, DELETE
AS
  declare @vmid int
  declare @vmname nvarchar(50)
  declare @ipaddr nvarchar(50)
  declare @old_capacity bigint
  declare @new_capacity bigint
  declare @new_vdevice_id int
  declare @old_vdevice_id int
  declare @new_update_key int
  declare @old_update_key int
  declare @lun_uuid nvarchar(255)
  --HARDWARE_DEVICE_CAPACITY_IN
BEGIN
    -- op_type:1=update,2=insert,3=delete,4=clone,5=relocate
	-- hd_type:cpu,mem,nic,disk,disk_space,vm,ip
    SET NOCOUNT ON;
	-- when disk inserted
	IF NOT EXISTS(SELECT * FROM Deleted)
	BEGIN
	    SELECT @vmid = vm_id, @new_vdevice_id = vdevice_id, @new_update_key = update_key, @new_capacity = CAST(HARDWARE_DEVICE_CAPACITY_IN AS bigint) FROM Inserted;
		SELECT @vmname = vm_name,@ipaddr = ip_addr FROM [dbo].[t_log_vm_state] where vm_id = @vmid;
		SELECT @lun_uuid = DEVICE_BACKING_LUN_UUID FROM [dbo].[VPX_VDEVICE_FILE_BACKING_X]  WHERE VM_ID = @vmid and UPDATE_KEY = @new_update_key;
		IF @ipaddr != '-1'
		BEGIN
		    INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value,vdevice_id,update_key,lun_uuid) values (@vmid,@vmname,@ipaddr,2,'disk_space',0,@new_capacity,@new_vdevice_id,@new_update_key,@lun_uuid);
		END
		ELSE
		    INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value,vdevice_id,update_key,lun_uuid) values (@vmid,@vmname,'-1',2,'disk_space',0,@new_capacity,@new_vdevice_id,@new_update_key,@lun_uuid);
    END	
	ELSE
    	-- when vm deleted
		IF NOT EXISTS(SELECT * FROM Inserted)
		BEGIN
		    SELECT @vmid = vm_id, @old_vdevice_id = vdevice_id, @old_update_key = update_key, @old_capacity = CAST(HARDWARE_DEVICE_CAPACITY_IN AS bigint) FROM Deleted;
			SELECT @vmname = vm_name,@ipaddr = ip_addr FROM [dbo].[t_log_vm_state] where vm_id = @vmid;
			SELECT @lun_uuid = lun_uuid FROM [dbo].[T_VM_EVENT] WHERE VM_ID = @vmid and UPDATE_KEY = @old_update_key and op_type = 2;
			INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value,vdevice_id,update_key,lun_uuid) values (@vmid,@vmname,@ipaddr,3,'disk_space',@old_capacity,0,@old_vdevice_id,@old_update_key,@lun_uuid);
		END
		ELSE
		    -- when vm config modified
            IF UPDATE(HARDWARE_DEVICE_CAPACITY_IN)
			BEGIN	        
	            SELECT @vmid = vm_id, @old_update_key = update_key, @old_capacity = CAST(HARDWARE_DEVICE_CAPACITY_IN AS bigint) FROM Deleted;
		        SELECT @vmname = vm_name,@ipaddr = ip_addr FROM [dbo].[t_log_vm_state] where vm_id = @vmid;
                SELECT @new_capacity = CAST(HARDWARE_DEVICE_CAPACITY_IN AS bigint),@new_vdevice_id = vdevice_id, @new_update_key = update_key FROM Inserted;
				SELECT @lun_uuid = lun_uuid FROM [dbo].[T_VM_EVENT] WHERE VM_ID = @vmid and UPDATE_KEY = @old_update_key and op_type = 2;
                IF @old_capacity <> @new_capacity
		        BEGIN
		            INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value,vdevice_id,update_key) values (@vmid,@vmname,@ipaddr,1,'disk_space',@old_capacity,@new_capacity,@new_vdevice_id,@new_update_key);
		        END
            END
            
END
GO


