CREATE TABLE public.settings (
	g_id int8 NOT NULL,
	prefix varchar NOT NULL DEFAULT '!'::character varying,
	CONSTRAINT settings_pk PRIMARY KEY (g_id)
);
