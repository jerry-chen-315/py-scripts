CREATE OR REPLACE FUNCTION func_vpx_virtual_disk()
  RETURNS trigger AS
$BODY$
DECLARE
  vmid integer;
  vmname varchar(50);
  ipaddr varchar(50);
  old_capacity bigint;
  new_capacity bigint;
  new_vdevice_id integer;
  old_vdevice_id integer;
  new_update_key integer;
  old_update_key integer;
  lun_uuid varchar(255);
  old_lun_uuid varchar(255);
BEGIN
	-- when disk inserted
	IF (TG_OP = 'INSERT') THEN
	    vmid := NEW.vm_id;
		new_vdevice_id := NEW.vdevice_id;
	    new_update_key := NEW.update_key;
		new_capacity := CAST(NEW.hardware_device_capacity_in AS bigint);
		SELECT ip_addr, vm_name INTO ipaddr, vmname FROM vc."t_log_vm_state" WHERE vm_id = vmid;
		SELECT device_backing_lun_uuid INTO lun_uuid FROM vpx_vdevice_file_backing_x WHERE vm_id = vmid and update_key = new_update_key;
		
		INSERT INTO t_vm_event(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value,vdevice_id,update_key,lun_uuid) VALUES (vmid,vmname,ipaddr,2,'disk_space',0,new_capacity,new_vdevice_id,new_update_key,lun_uuid);
	-- when vm deleted	
	ELSIF (TG_OP = 'DELETE') THEN
	    vmid := OLD.vm_id;
		old_vdevice_id := OLD.vdevice_id;
	    old_update_key := OLD.update_key;
		old_capacity := CAST(OLD.hardware_device_capacity_in AS bigint);
		SELECT ip_addr, vm_name INTO ipaddr, vmname FROM vc."t_log_vm_state" WHERE vm_id = vmid;
		SELECT lun_uuid INTO old_lun_uuid FROM t_vm_event WHERE vm_id = vmid and update_key = old_update_key and op_type = 2;
		INSERT INTO t_vm_event(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value,vdevice_id,update_key,lun_uuid) VALUES (vmid,vmname,ipaddr,3,'disk_space',old_capacity,0,old_vdevice_id,old_update_key,old_lun_uuid);
	-- when vm config modified	
	ELSIF (TG_OP = 'UPDATE' AND NEW.hardware_device_capacity_in IS NOT NULL) THEN
        vmid := NEW.vm_id;
		new_vdevice_id := NEW.vdevice_id;
	    new_update_key := NEW.update_key;
		new_capacity := CAST(NEW.hardware_device_capacity_in AS bigint);
		old_vdevice_id := OLD.vdevice_id;
	    old_update_key := OLD.update_key;
		old_capacity := CAST(OLD.hardware_device_capacity_in AS bigint);
		SELECT ip_addr, vm_name INTO ipaddr, vmname FROM vc."t_log_vm_state" WHERE vm_id = vmid;
		
		IF old_capacity <> new_capacity THEN
            INSERT INTO t_vm_event(vm_id,vm_name,ip_addr,op_type,hd_type,old_value,new_value,vdevice_id,update_key) VALUES (vmid,vmname,ipaddr,1,'disk_space',old_capacity,new_capacity,new_vdevice_id,new_update_key);
        END IF;
		
    END IF;        
END;
$BODY$ LANGUAGE plpgsql;

CREATE TRIGGER tr_vpx_virtual_disk AFTER INSERT OR DELETE OR UPDATE ON vc."vpx_virtual_disk"
    FOR EACH ROW EXECUTE PROCEDURE func_vpx_virtual_disk();


