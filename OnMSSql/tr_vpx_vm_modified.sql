USE [NewVCDB]
GO

/****** Object:  Trigger [dbo].[tr_vpx_vm_modified]    Script Date: 09/06/2018 10:10:06 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TRIGGER [dbo].[tr_vpx_vm_modified]
   ON [dbo].[VPX_VM]
   AFTER UPDATE, INSERT, DELETE
AS
  DECLARE @vmid int
  DECLARE @vmname nvarchar(50)
  DECLARE @var_count int
  DECLARE @ipaddr nvarchar(50)
  DECLARE @var_state nvarchar(50)
  DECLARE @new_ipaddr nvarchar(50)
  DECLARE @new_mem int
  DECLARE @new_cpu int
  DECLARE @new_nic int
  DECLARE @new_disk int
  DECLARE @new_guest_state nvarchar(50)
  DECLARE @old_mem int
  DECLARE @old_cpu int
  DECLARE @old_nic int
  DECLARE @old_disk int
  DECLARE @old_ipaddr nvarchar(50)
  DECLARE @old_guest_state nvarchar(50)
  --DECLARE @old_storage_space bigint
  
BEGIN
    -- #op_type:1=update,2=insert,3=delete,4=clone,5=relocate
	-- #hd_type:cpu,mem,nic,disk,disk_space,vm,ip
	-- #-1 = ip is null
	-- #-2 = vmname is null
	-- #table t_log_vm_state.status = drop, exist, create, init
    SET NOCOUNT ON;
	-- when vm inserted
	IF NOT EXISTS(SELECT * FROM Deleted)
	BEGIN
	    SELECT @vmid = ID FROM Inserted;
		--WAITFOR DELAY '00:00:02';
		--SELECT @vmname = NAME FROM [dbo].[VPX_VM_CONFIG_INFO] WHERE ID = @vmid;
		SELECT @new_mem = MEM_SIZE_MB FROM Inserted;
		SELECT @new_cpu = NUM_VCPU FROM Inserted;
		SELECT @new_nic = NUM_NIC FROM Inserted;
		SELECT @new_disk = NUM_DISK FROM Inserted;
		INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,'None','-1',2,'mem',0,@new_mem);
		INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,'None','-1',2,'cpu',0,@new_cpu);
		INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,'None','-1',2,'nic',0,@new_nic);
		INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,'None','-1',2,'disk',0,@new_disk);
		INSERT INTO [dbo].[t_log_vm_state](vm_id,vm_name,ip_addr,status,create_time,annotation) values (@vmid,'None','-1','create',GETUTCDATE(),'None');
    END		
	ELSE
    	-- #when vm deleted
		IF NOT EXISTS(SELECT * FROM Inserted)
		BEGIN
		    SELECT @vmid = ID FROM Deleted;
			SELECT @ipaddr = ip_addr,@vmname = vm_name FROM [dbo].[t_log_vm_state] WHERE vm_id = @vmid;
			--SELECT @vmname = vm_name FROM [dbo].[t_log_vm_state] WHERE vm_id = @vmid;
			SELECT @old_mem = MEM_SIZE_MB FROM Deleted;
		    SELECT @old_cpu = NUM_VCPU FROM Deleted;
		    SELECT @old_nic = NUM_NIC FROM Deleted;
		    SELECT @old_disk = NUM_DISK FROM Deleted;
			INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,@vmname,@ipaddr,3,'mem',@old_mem,0);
			INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,@vmname,@ipaddr,3,'cpu',@old_cpu,0);
			INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,@vmname,@ipaddr,3,'nic',@old_nic,0);
			INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,@vmname,@ipaddr,3,'disk',@old_disk,0);
			UPDATE [dbo].[t_log_vm_state] SET status = 'drop', drop_time = GETUTCDATE() WHERE vm_id = @vmid;
		END
		ELSE
		    -- #when vm config modified
            IF UPDATE(MEM_SIZE_MB) OR UPDATE(NUM_VCPU) OR UPDATE(NUM_NIC) OR UPDATE(NUM_DISK)
			BEGIN
	        
	            SELECT @vmid = ID FROM Deleted;
		        SELECT @vmname = vm_name, @ipaddr = ip_addr FROM [dbo].[t_log_vm_state] WHERE vm_id = @vmid;
		        SELECT @old_mem = MEM_SIZE_MB FROM Deleted;
		        SELECT @old_cpu = NUM_VCPU FROM Deleted;
		        SELECT @old_nic = NUM_NIC FROM Deleted;
		        SELECT @old_disk = NUM_DISK FROM Deleted;
		        SELECT @new_mem = MEM_SIZE_MB FROM Inserted;
		        SELECT @new_cpu = NUM_VCPU FROM Inserted;
		        SELECT @new_nic = NUM_NIC FROM Inserted;
		        SELECT @new_disk = NUM_DISK FROM Inserted;
				IF @vmname = 'None'
				BEGIN
				    --SELECT @vmname = name FROM [dbo].[VPX_VM_CONFIG_INFO] WHERE id = @vmid;
				    UPDATE [dbo].[t_log_vm_state] SET vm_name = @vmname WHERE vm_id = @vmid;
				    UPDATE [dbo].[T_VM_EVENT] SET new_value = @new_mem  WHERE vm_name = 'None' AND vm_id = @vmid AND hd_type = 'mem';
					UPDATE [dbo].[T_VM_EVENT] SET new_value = @new_cpu  WHERE vm_name = 'None' AND vm_id = @vmid AND hd_type = 'cpu';
					UPDATE [dbo].[T_VM_EVENT] SET new_value = @new_nic  WHERE vm_name = 'None' AND vm_id = @vmid AND hd_type = 'nic';
					UPDATE [dbo].[T_VM_EVENT] SET new_value = @new_disk WHERE vm_name = 'None' AND vm_id = @vmid AND hd_type = 'disk';
				END
                IF @old_mem <> @new_mem
		        BEGIN
		            INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,@vmname,@ipaddr,1,'mem',@old_mem,@new_mem);
		        END
		        IF @old_cpu <> @new_cpu
		        BEGIN
		            INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,@vmname,@ipaddr,1,'cpu',@old_cpu,@new_cpu);
		        END
		        IF @old_nic <> @new_nic
		        BEGIN
		            INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,@vmname,@ipaddr,1,'nic',@old_nic,@new_nic);
		        END
		        IF @old_disk <> @new_disk
		        BEGIN
		            INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (@vmid,@vmname,@ipaddr,1,'disk',@old_disk,@new_disk);
		        END
            END
            ELSE
            -- when vm ip modified
			    -- GUEST_STATE = running,notRunning
                IF UPDATE(IP_ADDRESS)
				BEGIN
				    SELECT @vmid = ID FROM Deleted;
					SELECT @vmname = NAME FROM [dbo].[VPX_VM_CONFIG_INFO] WHERE ID = @vmid;
					SELECT @new_ipaddr = IP_ADDRESS FROM Inserted;
					SELECT @new_guest_state = GUEST_STATE FROM Inserted;
					--SELECT @new_power_state = GUEST_STATE FROM Inserted;
					SELECT @old_ipaddr = IP_ADDRESS FROM Deleted;
					SELECT @old_guest_state = GUEST_STATE FROM Deleted;
					--SELECT @var_count = count(*) FROM [dbo].[t_log_vm_state] WHERE vm_id = @vmid AND status = 'create';
					SELECT @var_state = status FROM [dbo].[t_log_vm_state] WHERE vm_id = @vmid
					
					-- #update ip alter new vm startup , then set t_log_vm_state.status to running
					IF @var_state = 'create' AND @new_ipaddr LIKE '162%'
					BEGIN
						UPDATE [dbo].[T_VM_EVENT] SET ip_addr = @new_ipaddr WHERE vm_id = @vmid AND op_type = 2;
						UPDATE [dbo].[t_log_vm_state] SET status = 'exist', ip_addr = @new_ipaddr WHERE vm_id = @vmid;
					END
					--IF @var_state = 'init' AND @new_guest_state <> @old_guest_state AND @old_guest_state = 'notRunning' AND @new_ipaddr LIKE '162%'
					IF @var_state = 'init' AND @new_ipaddr LIKE '162%' 
					BEGIN
						UPDATE [dbo].[t_log_vm_state] SET status = 'exist', ip_addr = @new_ipaddr WHERE vm_id = @vmid;
					END
					-- update ip when modified, and guest_state is running
				    IF @new_ipaddr <> @old_ipaddr AND @new_guest_state = @old_guest_state
					BEGIN
					    INSERT INTO [dbo].[T_VM_EVENT](vm_id,vm_name,ip_addr,op_type,hd_type,comment) values (@vmid,@vmname,@new_ipaddr,1,'ip',@old_ipaddr);
						UPDATE [dbo].[t_log_vm_state] SET ip_addr = @new_ipaddr WHERE vm_id = @vmid;
						UPDATE [dbo].[T_VM_EVENT] SET ip_addr = @new_ipaddr WHERE vm_id = @vmid AND hd_type IN ('cpu','mem','nic','disk','disk_space');
					END

						
				END
END
GO


