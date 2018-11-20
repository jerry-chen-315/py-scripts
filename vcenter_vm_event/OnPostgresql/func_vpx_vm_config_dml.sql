CREATE OR REPLACE FUNCTION func_vpx_vm_config_info()
  RETURNS trigger AS
$BODY$
DECLARE
  vmid integer;
  vmname varchar(50);
  
BEGIN
    -- op_type:1=update,2=insert,3=delete,4=clone,5=relocate
	-- hd_type:cpu,mem,nic,disk,disk_space,vm,ip
	
	IF (TG_OP = 'INSERT') THEN
	    vmid := NEW.id;
		vmname := NEW.name;
		UPDATE t_vm_event SET vm_name = vmname WHERE vm_id = vmid AND vm_name = 'None' AND op_type = 2;
		UPDATE t_log_vm_state SET vm_name = vmname WHERE vm_id = vmid AND vm_name = 'None';
	END IF;
	RETURN NULL;
END;

$BODY$ LANGUAGE plpgsql;

CREATE TRIGGER tr_vpx_vm_config AFTER INSERT ON vc."vpx_vm_config_info"
    FOR EACH ROW EXECUTE PROCEDURE func_vpx_vm_config_info();