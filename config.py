# Fixed Project Constants
METER_TYPE = 1  # 1 = Chilled Water
WEATHER_YEAR = "2016"
DATABASE_URI = 'sqlite:///building_analytics.db'

# Fully decoded locations for the 16 sites in the ASHRAE dataset
SITE_COORDINATES = {
    0: (28.5383, -81.3792),   # Orlando, FL (University of Central Florida)
    1: (51.5074, -0.1278),    # London, UK (University College London)
    2: (33.4255, -111.9400),  # Tempe, AZ (Arizona State University)
    3: (38.9072, -77.0369),   # Washington, DC
    4: (37.8715, -122.2730),  # Berkeley, CA (UC Berkeley)
    5: (50.9097, -1.4044),    # Southampton, UK (University of Southampton)
    6: (38.9072, -77.0369),   # Washington, DC
    7: (45.4215, -75.6972),   # Ottawa, Canada (Carleton University)
    8: (28.5383, -81.3792),   # Orlando, FL
    9: (30.2672, -97.7431),   # Austin, TX (UT Austin)
    10: (41.2230, -111.9738), # Weber County, UT (Weber State University)
    11: (45.4215, -75.6972),  # Ottawa, Canada
    12: (53.3498, -6.2603),   # Dublin, Ireland
    13: (44.9778, -93.2650),  # Minneapolis, MN (University of Minnesota)
    14: (38.0293, -78.4767),  # Charlottesville, VA (University of Virginia)
    15: (42.4440, -76.5019)   # Ithaca, NY (Cornell University)
}