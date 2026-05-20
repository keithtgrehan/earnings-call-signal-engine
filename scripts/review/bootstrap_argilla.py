import argilla as rg

client = rg.Argilla(
    api_url="http://localhost:6900",
    api_key="argilla.apikey",
)

workspace_name = "signal-engine"

workspace = client.workspaces(workspace_name)

if workspace is None:
    workspace = rg.Workspace(name=workspace_name)
    workspace.create()

settings = rg.Settings(
    fields=[
        rg.TextField(
            name="text",
            title="Transcript Chunk",
            required=True,
        ),
    ],
    questions=[
        rg.MultiLabelQuestion(
            name="signals",
            title="Detected Signals",
            labels=[
                "guidance_revision",
                "tone_shift",
                "analyst_pressure",
                "uncertainty",
                "evasive_answer",
                "positive_surprise",
                "negative_surprise",
            ],
        ),
    ],
)

existing = client.datasets(name="earnings-call-review")

if existing is None:
    dataset = rg.Dataset(
        name="earnings-call-review",
        workspace=workspace.name,
        settings=settings,
    )
    dataset.create()
    print("Argilla dataset created successfully")
else:
    print("Dataset already exists")
