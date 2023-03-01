#!/usr/bin/env python
import gitlab
import datetime, logging, sys, os

logging.basicConfig(
  level    = logging.INFO,
  format   = "%(asctime)s [%(levelname)s] %(message)s",
  handlers = [
    logging.StreamHandler(sys.stdout)
  ]
)

URL    = os.getenv("GC_URL")
TOKEN  = os.getenv('GC_TOKEN')
WEEKS  = os.getenv("GC_WEEKS")
DRYRUN = os.getenv('GC_DRYRUN').lower()

class GITCleaner():
  def __init__(self):
    try:
      if URL is None:
        raise Exception("Environment variables missing! GC_URL is required!")
      
      if TOKEN is None:
        raise Exception("Environment variables missing! GC_TOKEN is required!")

      if WEEKS is None:
        raise Exception("Environment variables missing! GC_WEEKS is required!")

      if DRYRUN is None:
        raise Exception("Environment variables missing! GC_DRYRUN is required!")
    except Exception as e:
      logging.error(e)
      exit(1)

  def start(self):
    time_difference  = datetime.datetime.now() - datetime.timedelta(weeks=int(WEEKS))
    pipeline_keep    = 5 # dont delete last 5 pipelines

    gl = gitlab.Gitlab(URL, private_token=TOKEN)
    projects = gl.projects.list(get_all=True) # [gl.projects.get(739)]
    for project in projects:
      pipeline_total   = 0
      pipeline_deleted = 0

      project   = gl.projects.get(project.id)
      pipelines = project.pipelines.list(get_all=True)
      total_pipelines = len(pipelines)
      if total_pipelines <= 0 or total_pipelines <= pipeline_keep:
        logging.info(f'skiping of [{project.name_with_namespace}]')
        continue
      
      logging.info(f'deleting pipeline histories of [{project.name_with_namespace}]')
      
      project.artifacts.delete()

      project = gl.projects.get(project.id)
      for pipeline in project.pipelines.list(get_all=True):
        pipeline_total += 1
        if pipeline_keep >= pipeline_total:
          continue

        date = datetime.datetime.strptime(pipeline.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        if date < time_difference:
          pipeline_deleted += 1

          if DRYRUN == 'false':
            try:
              pipeline.delete()
            except:
              logging.error(f'403 forbiden - [{project.name_with_namespace}]')
              break
      
      logging.info(f'summary of [{project.name_with_namespace}] - Total:{pipeline_total}/Deleted:{pipeline_deleted}')


if __name__ == '__main__':
  state = "" if DRYRUN == 'false' else "(DRY RUN)"
  logging.info(f'Starting gitlab cleaner... {state}')

  cleaner = GITCleaner()
  cleaner.start()
  