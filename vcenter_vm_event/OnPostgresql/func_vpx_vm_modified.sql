CREATE OR REPLACE FUNCTION func_vpx_vm()
  RETURNS trigger AS
$BODY$
DECLARE
   vmid integer;
   vmname varchar(50);
   var_count integer;
   ipaddr varchar(50);
   var_state varchar(50);
   new_ipaddr varchar(50);
   new_mem integer;
   new_cpu integer;
   new_nic integer;
   new_disk integer;
   new_guest_state varchar(50);
   old_mem integer;
   old_cpu integer;
   old_nic integer;
   old_disk integer;
   old_ipaddr varchar(50);
   old_guest_state varchar(50);  
BEGIN
    -- #op_type:1=update,2=insert,3=delete,4=clone,5=relocate
	-- #hd_type:cpu,mem,nic,disk,disk_space,vm,ip
	-- #-1 = ip is null
	-- #-2 = vmname is null
	-- #table t_log_vm_state.status = drop, exist, create, init	
	-- when vm inserted
    IF (TG_OP = 'INSERT') THEN
	    vmid := NEW.id;
		new_mem := NEW.mem_size_mb;
        new_cpu := NEW.num_vcpu;
        new_nic := NEW.num_nic;
        new_disk := NEW.num_disk;
	    INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,'None','-1',2,'mem',0,new_mem);
		INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,'None','-1',2,'cpu',0,new_cpu);
		INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,'None','-1',2,'nic',0,new_nic);
		INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,'None','-1',2,'disk',0,new_disk);
		INSERT INTO vc."t_log_vm_state"(vm_id,vm_name,ip_addr,status,create_time,annotation) values (vmid,'None','-1','create',LOCALTIMESTAMP,'None');
	ELSIF (TG_OP = 'DELETE' AND OLD.num_vcpu IS NOT NULL) THEN
	    vmid := OLD.id;
		old_mem := OLD.mem_size_mb;
        old_cpu := OLD.num_vcpu;
        old_nic := OLD.num_nic;
        old_disk := OLD.num_disk;
		SELECT ip_addr, vm_name into ipaddr, vmname FROM vc."t_log_vm_state" WHERE vm_id = vmid;
		INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,vmname,ipaddr,3,'mem',old_mem,0);
		INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,vmname,ipaddr,3,'cpu',old_cpu,0);
		INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,vmname,ipaddr,3,'nic',old_nic,0);
		INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,vmname,ipaddr,3,'disk',old_disk,0);
		UPDATE vc."t_log_vm_state" SET status = 'drop', drop_time = LOCALTIMESTAMP WHERE vm_id = vmid;
    ELSIF (TG_OP = 'UPDATE' AND NEW.num_vcpu IS NOT NULL) THEN
	    vmid := OLD.id;
		new_mem := NEW.mem_size_mb;
        new_cpu := NEW.num_vcpu;
        new_nic := NEW.num_nic;
        new_disk := NEW.num_disk;
		old_mem := OLD.mem_size_mb;
        old_cpu := OLD.num_vcpu;
        old_nic := OLD.num_nic;
        old_disk := OLD.num_disk;
		SELECT ip_addr, vm_name into ipaddr, vmname FROM vc."t_log_vm_state" WHERE vm_id = vmid;		
		IF vmname = 'None' THEN
            UPDATE t_vm_event SET new_value = new_mem  WHERE vm_id = vmid AND hd_type = 'mem';
		    UPDATE t_vm_event SET new_value = new_cpu  WHERE vm_id = vmid AND hd_type = 'cpu';
		    UPDATE t_vm_event SET new_value = new_nic  WHERE vm_id = vmid AND hd_type = 'nic';
		    UPDATE t_vm_event SET new_value = new_disk WHERE vm_id = vmid AND hd_type = 'disk';
		END IF;
		IF old_mem != new_mem THEN
		    INSERT INTO t_vm_event(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,vmname,ipaddr,1,'mem',old_mem,new_mem);
		END IF;
		IF old_cpu != new_cpu THEN
		    INSERT INTO t_vm_event(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,vmname,ipaddr,1,'cpu',old_cpu,new_cpu);
		END IF;
		IF old_nic != new_nic THEN
		    INSERT INTO t_vm_event(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,vmname,ipaddr,1,'nic',old_nic,new_nic);
		END IF;
		IF old_disk != new_disk THEN
		    INSERT INTO t_vm_event(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value) values (vmid,vmname,ipaddr,1,'disk',old_disk,new_disk);
		END IF;
	ELSIF (TG_OP = 'UPDATE' AND NEW.GUEST_STATE IS NOT NULL) THEN
        vmid := OLD.id;
		new_ipaddr := NEW.IP_ADDRESS;
		new_guest_state := NEW.GUEST_STATE;
		old_ipaddr := OLD.IP_ADDRESS;
		old_guest_state := OLD.GUEST_STATE;
        SELECT vm_name,status into vmname,var_state FROM vc."t_log_vm_state" WHERE vm_id = vmid;
        IF var_state = 'create' AND new_ipaddr LIKE '162%' THEN
			UPDATE vc."t_vm_event" SET ip_addr = new_ipaddr WHERE vm_id = vmid AND op_type = 2;
			UPDATE vc."t_log_vm_state" SET status = 'exist', ip_addr = new_ipaddr WHERE vm_id = vmid;
		END IF;
		--IF var_state = 'init' AND new_guest_state <> old_guest_state AND old_guest_state = 'notRunning' AND new_ipaddr LIKE '162%'
		IF var_state = 'init' AND new_ipaddr LIKE '162%' THEN
			UPDATE vc."t_log_vm_state" SET status = 'exist', ip_addr = new_ipaddr WHERE vm_id = vmid;
		END IF;
		-- update ip when modified, and guest_state is running
		IF new_ipaddr <> old_ipaddr AND new_guest_state = old_guest_state THEN
		    INSERT INTO vc."t_vm_event"(vm_id,vm_name,ip_addr,op_type,hd_type,comment) values (vmid,vmname,new_ipaddr,1,'ip',old_ipaddr);
			UPDATE vc."t_log_vm_state" SET ip_addr = new_ipaddr WHERE vm_id = vmid;
			UPDATE vc."t_vm_event" SET ip_addr = new_ipaddr WHERE vm_id = vmid AND hd_type IN ('cpu','mem','nic','disk','disk_space');
		END IF;				
	END IF;
  RETURN NULL;
END;
$BODY$ LANGUAGE plpgsql;

CREATE TRIGGER tr_vpx_vm AFTER INSERT OR DELETE OR UPDATE ON vc."vpx_vm"
    FOR EACH ROW EXECUTE PROCEDURE func_vpx_vm();


