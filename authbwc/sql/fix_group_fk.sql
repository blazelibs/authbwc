alter table auth_user_group_map
add constraint fk_auth_ugmap_group_id
foreign key (auth_group_id) references auth_groups(id)
on delete cascade
