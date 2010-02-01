--statement-break
DROP VIEW IF EXISTS v_users_user_group_permissions

--statement-break
DROP VIEW IF EXISTS v_users_permissions

--statement-break
DROP VIEW IF EXISTS v_users_approved_group_permissions

--statement-break
DROP VIEW IF EXISTS v_users_denied_group_permissions

--statement-break
CREATE VIEW v_users_denied_group_permissions
AS
SELECT
  P.id as permission_id,
  UGM.users_user_id as user_id,
  sum(GAD.approved) as group_denied
FROM users_permission P
LEFT JOIN users_permission_assignments_groups GAD
  ON GAD.permission_id = P.id
  AND GAD.approved = -1
LEFT JOIN users_user_group_map UGM
  ON UGM.users_group_id = GAD.group_id
GROUP BY
  P.id,
  UGM.users_user_id

--statement-break
CREATE VIEW v_users_approved_group_permissions
AS
SELECT
  P.id as permission_id,
  UGM.users_user_id as user_id,
  sum(GAA.approved) as group_approved
FROM users_permission P
LEFT JOIN users_permission_assignments_groups GAA
  ON GAA.permission_id = P.id
  AND GAA.approved = 1
LEFT JOIN users_user_group_map UGM
  ON UGM.users_group_id = GAA.group_id
GROUP BY
  P.id,
  UGM.users_user_id

--statement-break
CREATE VIEW v_users_permissions
AS
SELECT 
  U.id as user_id,
  P.id  as permission_id,
  P.name as permission_name,
  U.login_id as login_id,
  UA.approved as user_approved,
  GA.group_approved as group_approved,
  GD.group_denied as group_denied
FROM users_user U
CROSS JOIN users_permission P
LEFT JOIN users_permission_assignments_users UA
  ON UA.user_id = U.id
  AND UA.permission_id = P.id
LEFT JOIN v_users_approved_group_permissions GA
  ON GA.user_id = U.id
  AND GA.permission_id = P.id
LEFT JOIN v_users_denied_group_permissions GD
  ON GD.user_id = U.id
  AND GD.permission_id = P.id
ORDER BY 
 U.id,
 P.id

--statement-break
CREATE VIEW v_users_user_group_permissions
AS
SELECT 
  U.id as user_id,
  G.id as group_id,
  G.name as group_name,
  GA.permission_id as permission_id,
  GA.approved as group_approved
FROM users_user U
LEFT JOIN users_user_group_map UGM
  ON UGM.users_user_id = U.id
LEFT JOIN users_group G
  ON G.id = UGM.users_group_id
LEFT JOIN users_permission_assignments_groups GA
  ON GA.group_id = G.id
WHERE permission_id IS NOT NULL
 
 