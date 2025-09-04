SELECT * FROM public.river_levels_bulletin
where  SPLIT_PART(unique_id,'_',2)::date BETWEEN '25.05.2025' AND '08.06.2025';
--where  SPLIT_PART(unique_id,'_',1) = '1' 
-- where SPLIT_PART(unique_id,'_',2) = '11.07.2025'
-- and SPLIT_PART(unique_id,'_',3) = 'Evening';
