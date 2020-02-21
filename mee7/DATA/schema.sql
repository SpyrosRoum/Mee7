CREATE TABLE public.settings (
	g_id int8 NOT NULL,
	prefix varchar NOT NULL DEFAULT '!'::character varying,
	welcome_chn_id int8 NULL,
	welcome_msg varchar NULL,
	CONSTRAINT settings_pk PRIMARY KEY (g_id)
);
