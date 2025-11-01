create table reports (
    game_id bigint primary key,
    game_date date default CURRENT_DATE,
    maka character varying(2),
    report_url text,
    delete_flg boolean default false,
    created_at timestamp default CURRENT_TIMESTAMP
);

create table statistics (
    game_id bigint primary key,
    my_score integer,
    my_rank integer,
    shimocha_score integer,
    shimocha_rank integer,
    toimen_score integer,
    toimen_rank integer,
    kamicha_score integer,
    kamicha_rank integer,
    rating double precision,
    total_reviewed integer,
    total_matches integer,
    total_bad integer,
    match_rate double precision,
    bad_rate double precision,
    dealin_count integer,
    dealin_shanten integer,
    delete_flg boolean default false,
    created_at timestamp default CURRENT_TIMESTAMP
);

create table settings (
    id integer primary key,
    item text,
    explain text,
    value integer,
    created_at timestamp default CURRENT_TIMESTAMP
);

insert into settings (
    item, 
    explain, 
    value
) 
values (
    'dealin_shanten_border', 
    'Mortalの推奨値がN[%]未満の時に悪手と判定する', 
    5
);