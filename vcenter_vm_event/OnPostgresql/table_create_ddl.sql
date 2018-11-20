CREATE TABLE vc.t_vm_event
(
    id integer NOT NULL DEFAULT nextval('t_vm_event_id_seq'::regclass),
    vm_id bigint,
    vm_name character varying(50) COLLATE pg_catalog."default",
    ip_addr character varying(50) COLLATE pg_catalog."default",
    op_type bigint,
    hd_type character varying(50) COLLATE pg_catalog."default",
    old_value bigint,
    new_value bigint,
    event_time timestamp without time zone DEFAULT ('now'::text)::timestamp without time zone,
    comment character varying(255) COLLATE pg_catalog."default",
    vdevice_id bigint,
    update_key bigint,
    lun_uuid character varying(255) COLLATE pg_catalog."default",
    CONSTRAINT t_vm_event_pkey PRIMARY KEY (id)
)

CREATE TABLE vc.t_log_vm_state
(
    create_time timestamp without time zone,
    drop_time timestamp without time zone,
    ip_addr character varying(50) COLLATE pg_catalog."default",
    status character varying(50) COLLATE pg_catalog."default",
    vm_id bigint NOT NULL,
    vm_name character varying(255) COLLATE pg_catalog."default",
    annotation character varying(300) COLLATE pg_catalog."default",
    CONSTRAINT p_vm_id PRIMARY KEY (vm_id)
)