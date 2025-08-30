import logging
import openai

# Configure logging for this module
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_user_dns_queries(connection, user_id: int, days_back: int = 100) -> List[Dict]:
        """
        Get DNS queries for a specific user over the last N days
        
        Args:
            user_id: The user ID to fetch queries for
            days_back: Number of days to look back (default: 30)
            
        Returns:
            List of DNS query records with domain information
        """
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Query to get DNS queries with domain information
            query = """
            SELECT 
                uq.id,
                uq.timestamp,
                uq.dns_server_ip,
                uq.cache_hit,
                uq.is_blocked,
                d.domain,
                d.category,
                d.is_unethical,
                uc.region,
                uc.country,
                uc.ip_address,
                uc.ISP
            FROM user_query uq
            JOIN user_connections uc ON uq.connection_id = uc.id
            JOIN domains d ON uq.domain = d.id
            WHERE uc.user_id = %s 
            AND uq.timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY uq.timestamp DESC
            """
            
            cursor.execute(query, (user_id, days_back))
            queries = cursor.fetchall()
            
            logger.info(f"Retrieved {len(queries)} DNS queries for user {user_id}")
            return queries
            
        except Error as err:
            logger.error(f"Error retrieving DNS queries: {err}")
            raise
    
def get_user_info(connection, user_id: int) -> Optional[Dict]:
        """Get user information by user ID"""
        try:
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT 
                u.id,
                u.os_type,
                u.username,
                u.browsing_profile,
                u.created_at,
                COUNT(DISTINCT uc.id) as connection_count,
                COUNT(DISTINCT uq.id) as query_count
            FROM users u
            LEFT JOIN user_connections uc ON u.id = uc.user_id
            LEFT JOIN user_query uq ON uc.id = uq.connection_id
            WHERE u.id = %s
            GROUP BY u.id
            """
            
            cursor.execute(query, (user_id,))
            user_info = cursor.fetchone()
            
            return user_info
            
        except Error as err:
            logger.error(f"Error retrieving user info: {err}")
            raise
    
def update_user_profile(connection, user_id: int, profile: str) -> bool:
        """Update user's browsing profile"""
        try:
            cursor = connection.cursor()
            
            query = "UPDATE users SET browsing_profile = %s WHERE id = %s"
            cursor.execute(query, (profile, user_id))
            connection.commit()
            
            logger.info(f"Updated profile for user {user_id}")
            return True
            
        except Error as err:
            logger.error(f"Error updating user profile: {err}")
            return False

def analyze_dns_patterns(self, dns_queries: List[Dict]) -> Dict:
        """
        Analyze DNS query patterns to extract behavioral insights
        
        Args:
            dns_queries: List of DNS query records
            
        Returns:
            Dictionary with analyzed patterns and statistics
        """
        if not dns_queries:
            return {
                'total_queries': 0,
                'unique_domains': 0,
                'categories': {},
                'time_patterns': {},
                'risk_indicators': []
            }
        
        # Basic statistics
        total_queries = len(dns_queries)
        unique_domains = len(set(query['domain'] for query in dns_queries))
        
        # Category analysis
        categories = {}
        unethical_count = 0
        blocked_count = 0
        
        for query in dns_queries:
            category = query.get('category', 'unknown')
            if category:
                categories[category] = categories.get(category, 0) + 1
            
            if query.get('is_unethical'):
                unethical_count += 1
            
            if query.get('is_blocked'):
                blocked_count += 1
        
        # Time pattern analysis
        hours = {}
        for query in dns_queries:
            if query.get('timestamp'):
                hour = query['timestamp'].hour
                hours[hour] = hours.get(hour, 0) + 1
        
        # Risk indicators
        risk_indicators = []
        if unethical_count > 0:
            risk_indicators.append(f"Accessed {unethical_count} potentially unethical domains")
        if blocked_count > 0:
            risk_indicators.append(f"{blocked_count} queries were blocked")
        
        risk_percentage = ((unethical_count + blocked_count) / total_queries) * 100 if total_queries > 0 else 0
        if risk_percentage > 10:
            risk_indicators.append(f"High risk activity: {risk_percentage:.1f}% of queries flagged")
        
        return {
            'total_queries': total_queries,
            'unique_domains': unique_domains,
            'categories': categories,
            'patterns': patterns,
            'time_patterns': hours,
            'risk_indicators': risk_indicators,
            'unethical_count': unethical_count,
            'blocked_count': blocked_count
        }
    
def classify_user_profile(user_info: Dict, dns_analysis: Dict) -> Dict:
    """
    Classify user profile based on DNS analysis and user info.
    """
    try:
        # Prepare context for OpenAI
        categories_str = ", ".join([f"{cat}: {count}" for cat, count in dns_analysis['categories'].items()])
        patterns_str = ", ".join([f"{k}: {v}" for k, v in dns_analysis['patterns'].items()])
            
        prompt = f"""
            Based on the following user data and DNS query analysis, create a comprehensive user persona and classification. 
            Identify the user type (e.g., gamer, student, business professional, researcher, general user) and provide insights.

            User Information:
            - OS: {user_info['os_type']}
            - Username: {user_info['username']}
            - Total Connections: {user_info['connection_count']}
            - Total Queries: {user_info['query_count']}

            DNS Analysis (Last 100 days):
            - Total DNS Queries: {dns_analysis['total_queries']}
            - Unique Domains: {dns_analysis['unique_domains']}
            - Domain Categories: {categories_str}
            - Risk Indicators: {'; '.join(dns_analysis['risk_indicators']) if dns_analysis['risk_indicators'] else 'None'}

            Please provide:
            1. User Classification: [Primary user type]
            2. Confidence Level: [High/Medium/Low]
            3. Key Characteristics: [List 3-5 key traits]
            4. Behavioral Insights: [2-3 sentences about browsing behavior]
            5. Risk Assessment: [Low/Medium/High with brief explanation]

            Format your response as a structured analysis.
            """

        logger.info(f"Generating persona for user {user_info['id']}...")
            
        response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using more cost-effective model
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert user behavior analyst specializing in digital footprint analysis. Provide accurate, professional assessments based on DNS query patterns."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
            
        persona = response.choices[0].message.content.strip()
        logger.info(f"Successfully generated persona for user {user_info['id']}")
            
        return persona
            
    except Exception as e:
            logger.error(f"Failed to generate persona for user {user_info['id']}: {str(e)}")
            return None

def generate_user_profile(connection, user_id, api_key):
    """
    Uses OpenAI to generate a persona based on user data.
    """
    user_info = get_user_info(connection, user_id)

    if not user_info:
                return {
                    'success': False,
                    'error': f'User {user_id} not found'
                }
            
    # Get DNS queries
    dns_queries = get_user_dns_queries(connection, user_id)
    dns_analysis = analyze_dns_patterns(dns_queries)
    return classify_user_profile(user_info, dns_analysis)

def update_user_profile(connection, api_key):
    """
    Fetches users, generates personas, and updates the database.
    """
    openai.api_key = api_key
    logger.info("Starting user persona update process...")
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()

        if not users:
            logger.info("No users found to process.")
            return

        logger.info(f"Found {len(users)} users for persona generation.")
        for user in users:
            user_id = user[0]
            new_user_profile = generate_user_profile(connection, user_id, api_key)

            if new_user_profile:
                update_user_profile(connection, user_id, new_user_profile)
            else:
                logger.warning(f"Skipping DB update for user {user_id} due to persona generation failure.")
    logger.info("User persona update process finished.")