class ValidateTcmsBlfUsers(APIView):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		results = []
		updated_count = 0
		api_url = os.getenv("TCMS_ENTITY_URL")
		if not api_url:
			return Response({"error": "TCMS_ENTITY_URL not configured"}, status=500)
		try:
			response = requests.get(api_url, verify=certifi.where(), timeout=30)
			response.raise_for_status()
			json_data = response.json()
		except Exception as e:
			return Response({"error": f"Failed to fetch TCMS data: {str(e)}"}, status=502)
		api_entities = []
		for entity in json_data.get("data", []):
			entity_details = entity.get("entity_details") or {}
			api_entities.append({
				"unit_name": entity.get("name", ""),
				"entity_name" : entity_details.get("name", ""),
				"user_name": entity_details.get("user_name", ""),
				"state": entity.get("state", ""),
				"district": entity.get("district", ""),
				"region_name": entity_details.get("region_name", ""),
				"whats_app_no" : entity_details.get("whats_app_no", ""),	
				"head_contact_name": entity.get("head_contact_name", ""),
				"head_contact_phone": entity.get("head_contact_phone", ""),
				"head_contact_email": entity.get("head_contact_email", ""),
				"tcmo_no" : entity.get("tcmo_no", ""),
				"unit_id": entity.get("unit_id", ""),
				"password": entity_details.get("actual_password", ""),
			})
		api_df = pd.DataFrame(api_entities)
		profiles = BlfProfile.cmobjects.all().values(
			"id", "entity_unit", "user__username", "region__region_name",
			"state__name", "district__name", "ho_contact_person",
			"ho_contact_number", "ho_contact_email", "profile_type",
		)
		profiles_df = pd.DataFrame(list(profiles))
		matched = fuzzymatcher.link_table(
			api_df,
			profiles_df,
			left_on=[
				"unit_name", "user_name", "state", "district",
				"unit_id", 
			],
			right_on=[
				"entity_unit", "user__username", "state__name", "district__name", "id",
			],
		)
		matched = matched.sort_values("match_score", ascending=False).drop_duplicates("unit_name")
		matched["match_score"] = matched["match_score"].fillna(0.0)
		matched_users_ids = []
		unmatched_users_ids = []
		for _, row in matched.iterrows():
			raw_score = row.get("match_score", 0.0)
			# print("raw_score ####", raw_score)
			if pd.isna(raw_score) or raw_score in ["nan", None]:
				raw_score = 0.0
			match_score = round(float(raw_score) * 100, 2)
			if str(row.get("unit_name", "")).strip().lower() == str(row.get("entity_unit", "")).strip().lower():
				match_score = 150.0
			elif (
				str(row.get("unit_name", "")).strip().lower() == str(row.get("entity_unit", "")).strip().lower()
				and str(row.get("state", "")).strip().lower() == str(row.get("state__name", "")).strip().lower()
				and str(row.get("district", "")).strip().lower() == str(row.get("district__name", "")).strip().lower()
			):
				match_score = 120.0
			user_update = "false"
			if match_score >= 0:
				profile_id = row.get("id", None)  
				update_data = BlfProfile.cmobjects.filter(id=profile_id).update(
					is_tcms_user=True,
					# tcms_unit_id=row.get("unit_id", ""),
					# tcmo_no=row.get("tcmo_no", ""),
				)
				if update_data:
					updated_count += 1
					user_update = "true"
					matched_users_ids.append(row.get("id"))
			else:
				unmatched_users_ids.append(row.get("id"))

			results.append({
				"tracetea_username": row.get("user__username", ""),
				"tcms_username": row.get("user_name", ""),
				"tracetea_entity_unit": row.get("entity_unit", ""),
				"tcms_entity": row.get("unit_name", ""),
				"tracetea_state": row.get("state__name", ""),
				"tcms_state": row.get("state", ""),
				"tracetea_district": row.get("district__name", ""),
				"tcms_district": row.get("district", ""),
				"match_score": sanitize_float(match_score),
				"user_update" : user_update
			})
			# generate_excel_blf(results)
		return Response({
			"count": len(results),
			"updated_count": updated_count,
			"results": results,
			"unmatched_users_ids" : set(unmatched_users_ids),
			"matched_users_ids" : set(unmatched_users_ids),
		})
