--Update records
UPDATE river_levels_bulletin
SET river = 'BRAHMAPUTRA'
WHERE SPLIT_PART(unique_id,'_',1) = '6'
and SPLIT_PART(unique_id,'_',2) = '11.07.2025'
and SPLIT_PART(unique_id,'_',3) = 'Evening'
and sl_no = '6';
--loop update
-- UPDATE river_levels_bulletin
-- SET unique_id = ( (SPLIT_PART(unique_id, '_', 1)::int + 1)::text || '_' || 
--                   SPLIT_PART(unique_id, '_', 2) || '_' || 
--                   SPLIT_PART(unique_id, '_', 3) )
-- WHERE SPLIT_PART(unique_id, '_', 2) = '11.07.2025'
--   AND SPLIT_PART(unique_id, '_', 3) = 'Evening'
--   AND SPLIT_PART(unique_id, '_', 1)::int BETWEEN 1 AND 28;