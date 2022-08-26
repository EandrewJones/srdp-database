from dotenv import load_dotenv
import requests
import pandas as pd
import math
import os


#
# Helper functions
#
def create_path(fname):
    current_dir = os.path.dirname(__file__)
    data_dir = "initial_migration_data"
    return os.path.join(current_dir, data_dir, fname)


class Config:
    def __init__(self, path_to_env="./.env"):
        # Source environment file
        load_dotenv(path_to_env)

        # Credentials
        self.username = os.environ.get("ADMIN_USERNAME") or "admin"
        self.password = os.environ.get("ADMIN_PASSWORD")

        # API info
        self.base_url = "https://srdp.ea-jones.com/api/"

        # Get initial token
        self.get_token()

    def get_token(self):
        assert (
            self.password is not None
        ), "Env file is missing or path to env is mis-specified"
        # TODO: Add auto refresh function by storing token as property
        r = requests.post(self.base_url + "tokens", auth=(self.username, self.password))
        try:
            self.token = r.json()["token"]
        except Exception as e:
            self.token = None
            raise e


def send_to_api(endpoint, payload, cfg):
    # Make post request
    assert cfg.token, "Config did not succesfully fetch authorization token."
    headers = {"Authorization": f"Bearer {cfg.token}"}
    r = requests.post(cfg.base_url + endpoint, json=payload, headers=headers)

    # Return status code
    print(r.status_code)


#
# Constants
#

data_and_endpoint_pairs = [
    (create_path("groups.csv"), "groups"),
    (create_path("orgs.csv"), "organizations"),
    (create_path("nonviolent_tactics.csv"), "nonviolent_tactics"),
    (create_path("violent_tactics.csv"), "violent_tactics"),
]

#
# Main
#
def main():
    # Instantiate API auth config
    cfg = Config()

    # Set constant batch size
    batch_size = 250

    # Iterate through data and endpoints
    for file_path, endpoint in data_and_endpoint_pairs:
        # Read in data and convert NaNs to None
        df = pd.read_csv(file_path)
        payload = df.where(pd.notnull(df), None).to_dict(orient="records")

        # Batch large payloads
        payload_size = len(payload)

        if payload_size > batch_size:
            n_batches = math.ceil(payload_size / batch_size)

            # Iterate through batches and send to api
            for i in range(n_batches):
                batch = payload[
                    i * batch_size : min(i * batch_size + batch_size, payload_size)
                ]
                # TODO: Add cariage return progress tracker
                send_to_api(endpoint, batch, cfg)
        else:
            send_to_api(endpoint, payload, cfg)


if __name__ == "__main__":
    main()
