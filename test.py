class ValidateTcmsBlfUsers(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):

        results = []
        updated_count = 0
        matched_users_ids = []
        unmatched_users_ids = []

        api_url = os.getenv("TCMS_ENTITY_URL")

        if not api_url:
            return Response(
                {"error": "TCMS_ENTITY_URL not configured"},
                status=500
            )

        # --------------------------------------------------
        # STEP 1: Fetch TCMS Data
        # --------------------------------------------------
        try:
            response = requests.get(
                api_url,
                verify=certifi.where(),
                timeout=30
            )
            response.raise_for_status()
            json_data = response.json()
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch TCMS data: {str(e)}"},
                status=502
            )

        api_entities = []

        for entity in json_data.get("data", []):
            entity_details = entity.get("entity_details") or {}

            api_entities.append({
                "unit_name": entity.get("name", "") or "",
                "user_name": entity_details.get("user_name", "") or "",
                "state": entity.get("state", "") or "",
                "district": entity.get("district", "") or "",
                "unit_id": str(entity.get("unit_id", "") or ""),
                "tcmo_no": entity.get("tcmo_no", "") or "",
            })

        if not api_entities:
            return Response({
                "count": 0,
                "updated_count": 0,
                "results": [],
                "message": "No TCMS data found"
            })

        api_df = pd.DataFrame(api_entities)

        # --------------------------------------------------
        # STEP 2: Fetch Local Profiles
        # --------------------------------------------------
        profiles = BlfProfile.cmobjects.all().values(
            "id",
            "entity_unit",
            "user__username",
            "state__name",
            "district__name",
        )

        profiles_df = pd.DataFrame(list(profiles))

        if profiles_df.empty:
            return Response({
                "count": 0,
                "updated_count": 0,
                "results": [],
                "message": "No BLF profiles found"
            })

        profiles_df["tcms_unit_id"] = profiles_df["tcms_unit_id"].astype(str)

        fuzzy_matches = fuzzymatcher.link_table(
            api_df_remaining,
            profiles_df_remaining,
            left_on=[
                "unit_name",
                "user_name",
                "state",
                "district",
            ],
            right_on=[
                "entity_unit",
                "user__username",
                "state__name",
                "district__name",
            ],
        )

        fuzzy_matches = (
            fuzzy_matches
            .sort_values("match_score", ascending=False)
            .drop_duplicates("unit_name")
        )

        fuzzy_matches["match_score"] = fuzzy_matches["match_score"].fillna(0.0)

        # --------------------------------------------------
        # STEP 7: UPDATE FUZZY MATCHES
        # --------------------------------------------------
        with transaction.atomic():

            for _, row in fuzzy_matches.iterrows():

                profile_id = row.get("id")
                raw_score = row.get("match_score", 0.0)

                if pd.isna(raw_score):
                    raw_score = 0.0

                match_score = round(float(raw_score) * 100, 2)

                if profile_id and match_score >= 0:

                    update_count = BlfProfile.cmobjects.filter(
                        id=profile_id
                    ).update(
                        is_tcms_user=True
                    )

                    if update_count:
                        updated_count += 1
                        matched_users_ids.append(profile_id)

                        results.append({
                            "profile_id": profile_id,
                            "match_type": "fuzzy",
                            "match_score": match_score,
                            "user_update": "true"
                        })
                else:
                    if profile_id:
                        unmatched_users_ids.append(profile_id)
        return Response({
            "count": len(results),
            "updated_count": updated_count,
            "results": results,
            "matched_users_ids": list(set(matched_users_ids)),
            "unmatched_users_ids": list(set(unmatched_users_ids)),
        })
